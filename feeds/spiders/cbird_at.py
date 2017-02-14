from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from feeds.loaders import CbirdFeedEntryItemLoader
from feeds.spiders import FeedsCrawlSpider


class CbirdAtSpider(FeedsCrawlSpider):
    name = 'cbird.at'
    allowed_domains = ['cbird.at']
    start_urls = ['http://cbird.at/hilfe/neu/', 'http://cbird.at/impressum']
    rules = (
        Rule(LinkExtractor(allow=('hilfe/neu/(\d+)',)), callback='parse_item'),
    )

    _title = 'Neue cbird Versionen',
    _subtitle = 'Die neuesten Versionen von cbird.'
    _link = start_urls[0]

    def parse_item(self, response):
        il = CbirdFeedEntryItemLoader(
            selector=response.xpath('//div[@class="main"]'),
            timezone='Europe/Vienna')
        il.add_xpath('title', 'h1/text()')
        il.add_value('link', response.url)
        il.add_xpath('content_html', 'h1/following-sibling::*')
        il.add_value('updated', response.url.split('/')[-1])
        il.add_value('author_name', self.name)
        yield il.load_item()

    def parse_imprint(self, response):
        self._author_name = (response.xpath(
            '//div[@class="main"]/p/text()').re_first('Firma (.*)') or
            self.name)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
