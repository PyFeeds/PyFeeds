#!/usr/bin/python3

import datetime
import json

from scrapy.spiders import Spider
import delorean
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class AtvAtSpider(Spider):
    name = 'atv.at'
    allowed_domains = ['atv.at']
    start_urls = ['http://atv.at/mediathek/neue-folgen/']

    _timezone = 'Europe/Vienna'
    _timerange = datetime.timedelta(days=7)

    def parse(self, response):
        il = FeedItemLoader()
        il.add_value('title', 'ATV.at')
        il.add_value('subtitle', 'Mediathek')
        il.add_value('link', 'http://atv.at')
        il.add_value('author_name', self.name)
        yield il.load_item()

        for link in response.css('.program_link').xpath('@href').extract():
            yield scrapy.Request(link, self.parse_item)

    def parse_item(self, response):
        # ATV.at is really hard to parse properly since there are so few clues
        # what is a link to a video and what not.
        # The easiest way is to look for the mod_teasers class, take the
        # parent section and use the id of that to feed an Ajax API. Sigh.
        for program_id in (response.xpath(
                "//section[child::div[@class and contains(concat(' ', "
                "normalize-space(@class), ' '), ' mod_teasers ')]]/@id").
                re('pi_(.*)')):
            yield scrapy.Request(
                response.urljoin('/uri/fepe/{}/?page=1'.format(program_id)),
                self.parse_video_links)

    def parse_video_links(self, response):
        for link in response.xpath('//a/@href').extract():
            yield scrapy.Request(link, self.parse_program)

    def parse_program(self, response):
        if not response.css('.jsb_video\/FlashPlayer'):
            return
        data = (
            json.loads(response.css('.jsb_video\/FlashPlayer').xpath(
                '@data-jsb').extract()[0])
        )
        data = (
            data['config']['initial_video']['parts'][0]['tracking']['nurago']
        )
        il = FeedEntryItemLoader(response=response,
                                 base_url='http://{}'.format(self.name),
                                 timezone=self._timezone,
                                 dayfirst=True)
        il.add_value('link', data['clipurl'])
        il.add_value('title', data['programname'])
        il.add_value('updated', data['airdate'])
        il.add_xpath('content_html', '//p[@class="plot_summary"]')
        item = il.load_item()
        # Only include videos posted in the last 7 days.
        if (item['updated'] + self._timerange >
                delorean.utcnow().shift(self._timezone)):
            yield item

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
