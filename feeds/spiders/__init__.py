import scrapy
from scrapy.spiders import CrawlSpider, Spider, XMLFeedSpider

from feeds.cache import FeedsCache
from feeds.utils import generate_feed_header


class FeedsSpider(Spider):
    def feed_headers(self):
        yield generate_feed_header(
            title=getattr(self, "feed_title", None),
            subtitle=getattr(self, "feed_subtitle", None),
            link=getattr(self, "feed_link", None),
            path=getattr(self, "path", None),
            author_name=getattr(self, "author_name", None),
            icon=getattr(self, "feed_icon", None),
            logo=getattr(self, "feed_logo", None),
        )

    def start_requests(self):
        for url in self.start_urls:
            # Don't cache start requests otherwise we never find new content.
            yield scrapy.Request(url, dont_filter=True, meta={"dont_cache": True})

    @property
    def cache(self):
        if getattr(self, "_cache", None) is None:
            self._cache = FeedsCache(self.settings)
        return self._cache


class FeedsCrawlSpider(CrawlSpider, FeedsSpider):
    pass


class FeedsXMLFeedSpider(XMLFeedSpider, FeedsSpider):
    pass
