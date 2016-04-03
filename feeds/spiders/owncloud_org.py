#!/usr/bin/python3

import datetime

import scrapy

from feeds.items import FeedItem
from feeds.items import FeedEntryItem


class OwncloudAtSpider(scrapy.Spider):
    name = 'owncloud.org'
    allowed_domains = ['owncloud.org']
    start_urls = ['https://owncloud.org/changelog/']

    def parse(self, response):
        yield FeedItem(
            title='ownCloud releases',
            subtitle='The latest releases of ownCloud.',
            link=self.start_urls[0],
            author={'name': self.name})

        for h3 in response.xpath('//main/h3'):
            item = FeedEntryItem(author={'name': self.name})
            item['title'] = h3.xpath(
                'normalize-space(text())').extract()[0]
            item['link'] = '{}#{}'.format(
                self.start_urls[0], item['title'].split()[1])
            item['updated'] = self._extract_datetime(
                h3.xpath('small/text()').extract()[0])
            item['content_html'] = h3.xpath(
                'following-sibling::ul').extract()[0]
            yield item

    def _extract_datetime(self, raw_date):
        # Strip chars from day and normalize months.
        parts = raw_date.split()
        parts[1] = ''.join((p for p in parts[1] if p.isdigit()))
        parts[0] = parts[0][0:3]
        return datetime.datetime.strptime(' '.join(parts), '%b %d %Y')

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
