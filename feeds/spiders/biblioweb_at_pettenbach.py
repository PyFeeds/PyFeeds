#!/usr/bin/python3

import datetime

import scrapy

from feeds.items import FeedItem
from feeds.items import FeedEntryItem


# TODO factor name out
class BibliowebAtPettenbachSpider(scrapy.Spider):
    _library = 'pettenbach'
    _library_user = 'Bibliothek {}'.format(_library.title())

    name = 'biblioweb.at/{}'.format(_library)
    allowed_domains = ['biblioweb.at']
    start_urls = ['http://www.biblioweb.at/{}/start.asp'.format(_library)]

    def parse(self, response):
        # Ignore the initial response to start.asp as it is required to get the
        # ASP cookie. Without this cookie the request to webopac123 (!) are
        # ignored and will be redirected to the "login" page.
        yield scrapy.Request(
            'http://www.biblioweb.at/webopac123/webopac.asp'
            '?kat=1&content=show_new&seit=60&order_by=Sachtitel',
            callback=self.parse_overview_page)

        yield FeedItem(
            title=self._library_user,
            subtitle='Neue Titel in der {}'.format(self._library_user),
            link='http://www.biblioweb.at/{}/'.format(self._library),
            author={'name': self._library_user})

    def parse_overview_page(self, response):
        # Find other pages
        for href in response.xpath(
                '//div[@id="p_main"][1]/div/a/div[@id!="p_aktuell"]/../@href'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, self.parse_overview_page)

        # Find content
        for href in response.xpath('//a[contains(@href, "mnr")]/@href'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, self.parse_content)

    def parse_content(self, response):
        parts = self._extract_parts(response)
        item = FeedEntryItem(author={'name': self._library_user})

        item['title'] = ' - '.join(parts[:self._find_first_meta(parts)])
        item['link'] = response.url
        item['updated'] = self._extract_datetime(response, parts)

        _content = ['<ul>']
        for part in parts:
            _content.append('<li>{}</li>'.format(part))
        _content.append('</ul>')
        item['content_html'] = ''.join(_content)
        yield item

    def _find_first_meta(self, parts):
        # Find the first entry after author | title | subtitle.
        for i, p in enumerate(parts):
            if p.count(',') == 2 or ':' in p:
                return i
        return len(parts)

    def _extract_parts(self, response):
        parts = [p.strip() for p in
                 response.xpath('//td/span/text()').extract()]
        return [p for p in parts if p not in ('', ', ,')]

    def _extract_datetime(self, response, parts):
        for part in parts:
            if part.startswith('In der Bibliothek seit:'):
                return datetime.datetime.strptime(part[-10:], '%d.%m.%Y')

        self.logger.error('No date found for: {}'.format(response.url))
        return datetime.datetime.now()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
