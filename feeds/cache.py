import hashlib
import logging
import os
import pickle
import shutil
from collections import defaultdict
from datetime import datetime, timezone
from time import time

import scrapy
from scrapy.extensions.httpcache import DummyPolicy, FilesystemCacheStorage
from scrapy.utils.python import to_bytes
from scrapy.utils.request import request_fingerprint

logger = logging.getLogger(__name__)


class FeedsCachePolicy(DummyPolicy):
    def should_cache_response(self, response, request):
        # We cache all responses regardless of HTTP code.
        return True


class FeedsCache:
    def __init__(self, settings):
        if settings.getbool("HTTPCACHE_ENABLED"):
            self.storage = FeedsCacheStorage(settings)
        else:
            self.storage = FeedsCacheInMemoryStorage()

    def get(self, spider, key):
        return self.storage.retrieve_object(spider, key)

    def set(self, spider, key, obj):
        return self.storage.store_object(spider, key, obj)

    def setdefault(self, spider, key, default_obj):
        obj = self.storage.retrieve_object(spider, key)
        if obj is not None:
            return obj
        self.storage.store_object(spider, key, default_obj)
        return default_obj

    def cleanup(self):
        self.storage.cleanup()


class FeedsCacheStorage(FilesystemCacheStorage):
    def __init__(self, settings):
        super().__init__(settings)
        # gzip is not supported
        self.use_gzip = False
        self._open = open
        self.ignore_http_codes = [
            int(x) for x in settings.getlist("HTTPCACHE_IGNORE_HTTP_CODES")
        ]

    def retrieve_response(self, spider, request):
        """Return response if present in cache, or None otherwise."""
        metadata = self._read_meta(spider, request)
        if metadata is not None and metadata["status"] in self.ignore_http_codes:
            # ignore cache entry for error responses
            logger.debug("Response for {} not cached".format(request))
            return
        # Retrieve response from cache.
        try:
            return super().retrieve_response(spider, request)
        finally:
            logger.debug("Retrieved response for {} from cache".format(request))

    def store_response(self, spider, request, response):
        """Store the given response in the cache."""
        # Read the old metadata.
        old_metadata = self._read_meta(spider, request)
        # This will overwrite old metadata (if there is one).
        super().store_response(spider, request, response)
        # Read the new metadata.
        metadata = self._read_meta(spider, request)
        # Add the parents' fingerprints to the metadata and merge the parents from the
        # old metadata. The last fingerprint is not included since it's the fingerprint
        # of this request.
        metadata["parents"] = list(
            set(request.meta["fingerprints"][:-1]).union(
                old_metadata["parents"] if old_metadata else []
            )
        )
        if request.meta.get("cache_expires") is not None:
            metadata["cache_expires"] = request.meta["cache_expires"].total_seconds()
        metadata["type"] = "response"
        # Write it back.
        rpath = self._get_request_path(spider, request)
        self._write_meta_to_path(rpath, metadata)

    def _get_request_path(self, spider, request):
        key = request_fingerprint(request, include_headers=["Cookie"])
        return os.path.join(self.cachedir, spider.name, key[0:2], key)

    def retrieve_object(self, spider, key):
        metadata = self._read_meta(spider, key)
        if metadata is None:
            return None
        path = self._get_key_path(spider, key)
        with self._open(os.path.join(path, "object"), "rb") as f:
            return pickle.load(f)

    def store_object(self, spider, key, obj):
        path = self._get_key_path(spider, key)
        if not os.path.exists(path):
            os.makedirs(path)
        metadata = {"timestamp": time(), "type": "object"}
        self._write_meta_to_path(path, metadata)
        with self._open(os.path.join(path, "object"), "wb") as f:
            pickle.dump(obj, f, protocol=2)

    def _get_key_path(self, spider, key):
        key = hashlib.sha1(to_bytes(key)).hexdigest()
        return os.path.join(self.cachedir, spider.name, key[0:2], key)

    def remove_response(self, response, spider):
        self.remove_cache_entry(
            self._get_request_path(spider, response.request), remove_parents=True
        )

    def _read_meta(self, spider, key):
        if isinstance(key, scrapy.Request):
            path = self._get_request_path(spider, key)
        else:
            path = self._get_key_path(spider, key)
        return self._read_meta_from_path(path)

    def _read_meta_from_path(self, path):
        try:
            with open(os.path.join(path, "pickled_meta"), "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return None

    def _write_meta_to_path(self, path, metadata):
        with self._open(os.path.join(path, "meta"), "wb") as f:
            f.write(to_bytes(repr(metadata)))
        with self._open(os.path.join(path, "pickled_meta"), "wb") as f:
            pickle.dump(metadata, f, protocol=2)

    def cleanup(self):
        """Removes cache entries in path.

        Entries are removed if one of the conditions is true:
          - Response has a certain status code (e.g. 404).
          - Individual expiration date is reached (compared to now).
          - Timestamp of entry and expires exceeds now.
        """

        logger.debug("Cleaning cache entries from {} ...".format(self.cachedir))

        now = int(datetime.now(timezone.utc).timestamp())
        for cache_entry_path, _dirs, files in os.walk(self.cachedir, topdown=False):
            if "pickled_meta" in files:
                meta = self._read_meta_from_path(cache_entry_path)
                entry_expires_after = min(
                    meta.get("cache_expires", self.expiration_secs),
                    self.expiration_secs,
                )
                threshold = meta["timestamp"] + entry_expires_after
                if now > threshold:
                    self.remove_cache_entry(cache_entry_path)
                elif (
                    meta.get("type", "response") == "response"
                    and meta["status"] in self.ignore_http_codes
                ):
                    self.remove_cache_entry(cache_entry_path, remove_parents=True)
            elif not os.path.samefile(cache_entry_path, self.cachedir):
                # Try to delete parent directory of cache entries.
                try:
                    os.rmdir(cache_entry_path)
                except OSError:
                    # Not empty, don't care.
                    pass

        logger.debug("Finished cleaning cache entries.")

    def remove_cache_entry(self, cache_entry_path, remove_parents=False):
        meta = self._read_meta_from_path(cache_entry_path)
        if meta is None:
            return

        if remove_parents and "parents" in meta:
            spider_root = os.path.dirname(os.path.dirname(cache_entry_path))
            for fingerprint in meta["parents"]:
                path = os.path.join(spider_root, fingerprint[0:2], fingerprint)
                self.remove_cache_entry(path, remove_parents=False)

        shutil.rmtree(cache_entry_path, ignore_errors=True)


class FeedsCacheInMemoryStorage:
    def __init__(self):
        self.data = defaultdict(dict)

    def retrieve_object(self, spider, key):
        return self.data[spider].get(key)

    def store_object(self, spider, key, obj):
        self.data[spider][key] = obj

    def cleanup(self):
        pass
