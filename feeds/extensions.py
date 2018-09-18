import logging
import os
import pickle

from scrapy.extensions.httpcache import FilesystemCacheStorage
from scrapy.utils.python import to_bytes
from scrapy.utils.request import request_fingerprint

from feeds.cache import IGNORE_HTTP_CODES, remove_cache_entry


logger = logging.getLogger(__name__)


class FeedsCacheStorage(FilesystemCacheStorage):
    def __init__(self, settings):
        super().__init__(settings)
        # gzip is not supported
        self.use_gzip = False
        self._open = open

    def retrieve_response(self, spider, request):
        """Return response if present in cache, or None otherwise."""
        metadata = self._read_meta(spider, request)
        if metadata is not None and metadata["status"] in IGNORE_HTTP_CODES:
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
        if (
            "cache_expires" in request.meta
            and request.meta["cache_expires"] is not None
        ):
            metadata["cache_expires"] = request.meta["cache_expires"].total_seconds()
        # Write it back.
        rpath = self._get_request_path(spider, request)
        with self._open(os.path.join(rpath, "meta"), "wb") as f:
            f.write(to_bytes(repr(metadata)))
        with self._open(os.path.join(rpath, "pickled_meta"), "wb") as f:
            pickle.dump(metadata, f, protocol=2)

    def _get_request_path(self, spider, request):
        key = request_fingerprint(request, include_headers=["Cookie"])
        return os.path.join(self.cachedir, spider.name, key[0:2], key)

    def item_dropped(self, item, response, exception, spider):
        remove_cache_entry(
            self._get_request_path(spider, response.request), remove_parents=True
        )
