#!/usr/bin/python3

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider
from scrapy.spiders import Rule

from feeds.loaders import FeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class TipsAtSpider(CrawlSpider):
    name = "tips.at"
    allowed_domains = ["tips.at"]
    start_urls = ['http://www.tips.at/gewinnspiele/']
    rules = (
        Rule(LinkExtractor(allow=('gewinnspiele/\?page',))),
        Rule(LinkExtractor(
            allow=('service/impressum',)), callback='parse_imprint'),
        Rule(LinkExtractor(
            allow=('gewinnspiele/',), deny=('gewinnspiele/gewinner',)),
            callback='parse_item')
    )

    def parse_item(self, response):
        il = FeedEntryItemLoader(response=response,
                                 base_url='http://{}'.format(self.name),
                                 remove_elems=['script'],
                                 timezone='Europe/Vienna',
                                 dayfirst=True)
        il.add_value('link', response.url)
        il.add_xpath('title', '//h1[@class="article-title"]/text()')
        il.add_xpath('author_name', '//div[@class="calendar-time"]/a/text()')
        il.add_value(
            'content_html', 'Region: {}'.format(
                response.url.split('/')[4].title()))
        il.add_xpath('content_html', '//div[@class="shortcode-content"]')
        il.add_xpath(
            'content_html', '//div[@class="main-article-content"]//img')
        il.add_xpath(
            'updated', '//div[@class="calendar-time"]/text()',
            re='läuft bis ([^\s]+)')
        yield il.load_item()

    def parse_imprint(self, response):
        # Do not actually parse anything in here, but workaround the fact that
        # start_requests() does not allow to yield items.
        il = FeedItemLoader()
        il.add_value('title', 'Tips Gewinnspiele')
        il.add_value('subtitle', 'Aktuelle Gewinnspiele von Tips.')
        il.add_value('link', self.start_urls[0])
        il.add_value('author_name', self.name)
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
