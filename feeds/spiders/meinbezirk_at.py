#!/usr/bin/python3

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider
from scrapy.spiders import Rule

from feeds.loaders import FeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class MeinbezirkAtSpider(CrawlSpider):
    _emitted_feed_item = False

    name = "meinbezirk.at"
    allowed_domains = ["meinbezirk.at"]
    start_urls = ['http://www.meinbezirk.at/themen/gewinnspiel.html']
    rules = (
        # Limit to the first 9 pages only, the stuff that follows afterwards is
        # most likely expired already.
        Rule(LinkExtractor(
            allow=('themen/gewinnspiel.html/action/page/\d',),
            deny=('themen/gewinnspiel.html/action/page/\d\d+',))),
        Rule(LinkExtractor(
            restrict_xpaths='//div[@id="contentArea"]'),
            callback='parse_item')
    )

    def parse_item(self, response):
        # Ignore all articles without lottery or with an expired lottery.
        if not response.xpath(
                '//div[@id="contentArea"]//text()').re('Jetzt mitmachen'):
            return

        # One FeedItem is required.
        if not self._emitted_feed_item:
            self._emitted_feed_item = True
            il = FeedItemLoader(response=response)
            il.add_value('title', 'Meinbezirk Gewinnspiele')
            il.add_value('subtitle', 'Aktuelle Gewinnspiele von Meinbezirk.')
            il.add_value('link', self.start_urls[0])
            il.add_xpath('author_name', '//head/meta[@name="author"]/@content')
            il.add_value('author_name', self.name)
            yield il.load_item()

        # Parse the actual content.
        il = FeedEntryItemLoader(response=response,
                                 timezone='Europe/Vienna',
                                 dayfirst=True,
                                 remove_elems=['script', 'iframe'])
        il.add_value('link', response.url)
        il.add_xpath('title', '//div[@id="contentArea"]//h1/text()')
        il.add_xpath('title', '//div[@id="breadcrumbs"]/div/text()')
        il.add_xpath('title', '//head/meta[@property="og:title"]/@content')
        il.add_xpath('author_name', '//head/meta[@name="author"]/@content')
        il.add_xpath('author_name', '//head/meta[@name="publisher"]/@content')
        il.add_xpath('updated',
                     '//div[@class="marginBottomS"]/text()', re='(.*) Uhr')
        il.add_xpath('content_html', '//section[@id="articleContent"]')
        il.add_xpath('content_html', '//div[@id="lotteryArea"]/h3//text()')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
