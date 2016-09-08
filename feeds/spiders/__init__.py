from scrapy.spiders import CrawlSpider
from scrapy.spiders import Spider
from scrapy.spiders import XMLFeedSpider

from feeds.loaders import FeedItemLoader


class FeedsSpider(Spider):

    def generate_feed_header(self, title=None, subtitle=None, link=None,
                             path=None, author_name=None, icon=None,
                             logo=None):
        il = FeedItemLoader()
        il.add_value('title', title or getattr(self, '_title', self.name))
        il.add_value('subtitle', subtitle or getattr(self, '_subtitle', None))
        il.add_value(
            'link',
            link or getattr(self, '_link', 'http://www.{}'.format(self.name)))
        il.add_value('path', path or getattr(self, '_path', None))
        il.add_value(
            'author_name', author_name or getattr(self, '_author_name', title))
        il.add_value('icon', icon or getattr(self, '_icon', None))
        il.add_value('logo', logo or getattr(self, '_logo', None))
        return il.load_item()

    def feed_headers(self):
        return self.generate_feed_header()


class FeedsCrawlSpider(CrawlSpider, FeedsSpider):
    pass


class FeedsXMLFeedSpider(XMLFeedSpider, FeedsSpider):
    pass
