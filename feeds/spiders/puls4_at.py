#!/usr/bin/python3

from datetime import datetime
from datetime import timedelta
from urllib.parse import urljoin
import re

from scrapy.spiders import Spider
from scrapy.loader.processors import TakeFirst
import delorean
import js2xml
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class Puls4ComSpider(Spider):
    name = 'puls4.com'
    allowed_domains = ['puls4.com']

    _emitted_feed_item = False
    _timezone = 'Europe/Vienna'
    _max_days = 2

    def start_requests(self):
        start = datetime.utcnow() - timedelta(days=self._max_days - 1)
        for day in delorean.range_daily(start=start, count=self._max_days,
                                        timezone='UTC'):
            yield scrapy.Request(
                'http://www.{}/video/dateSearch?f[date]={}&f[channel_id]=&'
                'gsa_collection_id=videos'.format(
                    self.name,
                    day.shift(self._timezone).format_datetime('d.M.Y')),
                self._parse_archive_page)

    def _parse_archive_page(self, response):
        if not self._emitted_feed_item:
            self._emitted_feed_item = True
            il = FeedItemLoader()
            il.add_value('title', 'puls4')
            il.add_value('subtitle',
                         'Das TV-Videoportal')
            il.add_value('link', 'http://www.{}.com'.format(self.name))
            il.add_value('author_name', self.name)
            yield il.load_item()

        for episode in response.css('.span-18'):
            link = episode.xpath(
                ".//a[child::div[@class and contains(concat(' ', "
                "normalize-space(@class), ' '), ' bg_fullShowT3 ')]]/"
                "@href"
                ).extract_first()
            airdate = response.xpath('//h1/text()').re_first(
                r'(\d{2}\.\d{2}\.\d{4})')
            if not link:
                links = [
                    l.xpath('@href').extract_first()
                    for l in episode.css('a.bg_relativeBlock')
                    if 'Trailer' not in l.xpath('img/@title').extract_first()
                ]
                if len(links) == 1:
                    link = links[0]
                    self.logger.debug('Assuming {} is full video link'.format(
                        link))
                else:
                    self.logger.debug('No full video link for episode found. '
                                      'Creating item for program instead.')
                    yield self._create_episode_elem(episode, airdate)
                    continue
            yield scrapy.Request(response.urljoin(link), self._parse_item,
                                 meta={'airdate': airdate})

    def _parse_item(self, response):
        real_url = response.css('.fsk-button a::attr(href)').extract_first()
        if real_url:
            return scrapy.Request(real_url, self._parse_item,
                                  dont_filter=True, meta=response.meta)

        remove_elems = [
            '.bg_socialise', '.bg_videoBig', '.bg_imgMargin', '.clear',
            '.bg_marginer', 'strong'
        ]
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='http://{}'.format(self.name),
                                 remove_elems=remove_elems,
                                 dayfirst=True)
        error = response.css('.message-error').extract_first()
        if not error:
            js = js2xml.parse(response.xpath(
                "//script[contains(.,'files.puls4.com')]/text()"
                ).extract_first())
            updated = scrapy.Selector(root=js).xpath(
                '//property[@name="airdate"]/string/text()').extract_first()
        else:
            # Video not available, most likely geoblocked.
            il.add_value('content_html', error)
            il.add_value('category', 'geoblocked')
            # Heuristic to get airdate.
            today = response.css('.bg_tag::text').re_first('Sendung vom (.*)')
            next_episode = response.css('.bg_next::text').re_first(
                r'(\d{2}:\d{2})')
            updated = '{} {}'.format(today, next_episode or '')
        il.add_value('updated', updated)
        airdate = delorean.parse(response.meta['airdate'], dayfirst=True)
        updated = delorean.parse(updated, dayfirst=True)
        if updated < airdate:
            self.logger.debug(
                'Skipping {} which was originally aired {} (and reaired {}).'.
                format(response.url, updated.humanize(), airdate.humanize()))
            return
        il.add_value('link', response.url)
        regex = re.compile(r'(.*?)(?:vom \d{2}\.\d{2}\.\d{4}|$)', re.DOTALL)
        il.add_value('title', response.css('h1::text').re_first(regex))
        il.add_css('content_html', '.bg_videoBox')
        il.add_css('category', '.bg_tag::text', TakeFirst())
        return il.load_item()

    def _create_episode_elem(self, episode, airdate):
        il = FeedEntryItemLoader(timezone=self._timezone,
                                 base_url='http://{}'.format(self.name),
                                 dayfirst=True)
        updated = '{} {}'.format(
            airdate,
            episode.xpath('preceding-sibling::h3/text()').extract_first())
        il.add_value('updated', updated)
        link = urljoin('http://www.{}'.format(self.name), episode.xpath(
            'preceding-sibling::h3/a/@href').extract_first())
        il.add_value('link', link)
        title = episode.xpath(
            'preceding-sibling::h3/a/text()').extract_first()
        il.add_value('title', title)
        return il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
