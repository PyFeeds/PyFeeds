import os

import pickle
from scrapy import signals
from scrapy.extensions.httpcache import FilesystemCacheStorage
from scrapy.utils.python import to_bytes

from feeds.cache import IGNORE_HTTP_CODES


class SpiderSettings:
    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        return ext

    def spider_opened(self, spider):
        spider.spider_settings = self.spider_settings(spider)

    @classmethod
    def spider_settings(cls, spider):
        return spider.settings.get("FEEDS_CONFIG").get(spider.name, {})


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
            return  # ignore cache entry for error responses
        # Retrieve response from cache.
        return super().retrieve_response(spider, request)

    def store_response(self, spider, request, response):
        """Store the given response in the cache."""
        # Read the old metadata.
        old_metadata = self._read_meta(spider, request)
        # This will overwrite old metadata (if there is one).
        super().store_response(spider, request, response)
        # Read the new metadata.
        metadata = self._read_meta(spider, request)
        # Add the parents' fingerprints to the metadata and merge the parents from the
        # old metadata.
        metadata["parents"] = list(
            set(request.meta["fingerprints"]).union(
                old_metadata["parents"] if old_metadata else []
            )
        )
        # Write it back.
        rpath = self._get_request_path(spider, request)
        with self._open(os.path.join(rpath, "meta"), "wb") as f:
            f.write(to_bytes(repr(metadata)))
        with self._open(os.path.join(rpath, "pickled_meta"), "wb") as f:
            pickle.dump(metadata, f, protocol=2)
