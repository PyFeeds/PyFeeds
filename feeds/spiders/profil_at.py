#!/usr/bin/python3

import datetime

from scrapy.spiders import Spider
import pytz
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class ProfilAtSpider(Spider):
    name = 'profil.at'
    allowed_domains = ['profil.at']

    _emitted_feed_item = False
    _datetime_format = '%Y-%m-%dT%H:%M:%S'
    _timezone = pytz.timezone('Europe/Vienna')
    _max_days = 3

    def start_requests(self):
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC).astimezone(
            self._timezone)
        for day in range(self._max_days):
            yield scrapy.Request(
                'http://{}/archiv/{}'.format(
                    self.name, (now - datetime.timedelta(days=day)).strftime(
                        '%Y/%m/%d')), self.parse_archive_page)

    def parse_archive_page(self, response):
        if not self._emitted_feed_item:
            self._emitted_feed_item = True
            il = FeedItemLoader()
            il.add_value('title', 'PROFIL')
            il.add_value('subtitle',
                         'Österreichs unabhängiges Nachrichtenmagazin')
            il.add_value('link', 'http://www.profil.at')
            il.add_value('author_name', self.name)
            yield il.load_item()

        for link in response.xpath('//h1/a/@href').extract():
            yield scrapy.Request(response.urljoin(link), self.parse_item)

    def parse_item(self, response):
        remove_elems = [
            'aside', 'script', 'h1', '.breadcrumbs', '.author-date',
            '.artikel-social-kommentar', '.bild-copyright',
            '.ressortTitleMobile', '.article-number', '.artikel-kommentarlink'
        ]
        il = FeedEntryItemLoader(response=response,
                                 datetime_format=self._datetime_format,
                                 timezone=self._timezone,
                                 base_url='http://{}'.format(self.name),
                                 remove_elems=remove_elems)
        il.add_value('link', response.url)
        il.add_xpath('author_name', '//a[@rel="author"]/text()')
        il.add_xpath(
            'author_name', 'substring-before(substring-after('
            '(//section[@class="author-date"]/text())[1]'
            ', "Von"), "(")')
        il.add_value('author_name', 'Red.')
        il.add_xpath('title', '//h1/text()')
        il.add_xpath(
            'updated', 'substring-before('
            '//meta[@property="article:published_time"]/@content'
            ', "+")')
        il.add_xpath('content_html', '//article')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
