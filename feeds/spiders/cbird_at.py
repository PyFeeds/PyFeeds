#!/usr/bin/python3

import datetime

import scrapy

from feeds.items import FeedEntryItem
from feeds.items import FeedItem


class CbirdAtSpider(scrapy.Spider):
    name = 'cbird.at'
    allowed_domains = ['cbird.at']
    start_urls = ['http://cbird.at/hilfe/neu/']

    def parse(self, response):
        yield FeedItem(
            title='Neue cbird Versionen',
            subtitle='Die neuesten Versionen von cbird.',
            link=self.start_urls[0],
            author={'name': self.name})

        for href in response.xpath(
                '//table[@class="act"]//*[string(@href)]/@href'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, callback=self.parse_announcement)

    def parse_announcement(self, response):
        sel = response.xpath('//div[@class="main"]')
        item = FeedEntryItem(author={'name': self.name})
        item['title'] = sel.xpath('h1/text()').extract()[0]
        item['link'] = response.url
        item['updated'] = datetime.datetime.strptime(
            response.url.split('/')[-1], '%Y%m%d')
        item['content_html'] = ''.join(
            sel.xpath('h1/following-sibling::*').extract())
        yield item

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
