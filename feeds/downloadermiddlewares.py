from scrapy import signals
from scrapy.downloadermiddlewares.httpcache import HttpCacheMiddleware


class FeedsHttpCacheMiddleware(HttpCacheMiddleware):
    @classmethod
    def from_crawler(cls, crawler):
        o = super().from_crawler(crawler)
        crawler.signals.connect(o.item_dropped, signal=signals.item_dropped)
        return o

    def item_dropped(self, item, response, exception, spider):
        self.storage.remove_response(response, spider)
