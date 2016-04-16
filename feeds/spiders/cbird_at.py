#!/usr/bin/python3

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider
from scrapy.spiders import Rule

from feeds.loaders import CbirdFeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class CbirdAtSpider(CrawlSpider):
    name = 'cbird.at'
    allowed_domains = ['cbird.at']
    start_urls = ['http://cbird.at/hilfe/neu/']
    rules = (
        Rule(LinkExtractor(allow=('hilfe/neu/(\d+)',)), callback='parse_item'),
        Rule(LinkExtractor(allow=('impressum',)), callback='parse_imprint'),
    )

    def parse_item(self, response):
        il = CbirdFeedEntryItemLoader(
            selector=response.xpath('//div[@class="main"]'),
            datetime_format='%Y%m%d')
        il.add_xpath('title', 'h1/text()')
        il.add_value('link', response.url)
        il.add_xpath('content_html', 'h1/following-sibling::*')
        il.add_value('updated', response.url.split('/')[-1])
        il.add_value('author_name', self.name)
        yield il.load_item()

    def parse_imprint(self, response):
        il = FeedItemLoader(response=response)
        il.add_value('title', 'Neue cbird Versionen')
        il.add_value('subtitle', 'Die neuesten Versionen von cbird.')
        il.add_value('link', self.start_urls[0])
        il.add_xpath('author_name',
                     '//div[@class="main"]/p/text()', re='Firma (.*)')
        il.add_value('author_name', self.name)
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
