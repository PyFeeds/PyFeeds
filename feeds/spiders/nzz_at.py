import json

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class NzzAtSpider(FeedsSpider):
    name = 'nzz.at'
    allowed_domains = ['nzz.at', 'track.nzz.ch']

    _title = 'NZZ.at'
    _link = 'https://nzz.at'
    _subtitle = 'Hintergrund, Analyse, Kommentar'
    _timezone = 'Europe/Vienna'
    _logo = 'https://nzz.at/wp-content/themes/flair/img/apple-touch-icon.png'
    _icon = 'https://nzz.at/wp-content/themes/flair/favicon.ico'

    _max_items = 3  # for each ressort
    _track_url = 'https://track.nzz.ch/cam-1.0/api/auth_v3/public/{}/xhr'
    _login_url = 'https://login.nzz.at/cam-1.0/api/auth_v3/public/{}/xhr'
    _headers = {
        'Content-Type': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
    }

    def start_requests(self):
        username = self.spider_settings.get('username')
        password = self.spider_settings.get('password')
        if username and password:
            self._login_data = {
                'password': password,
                'login': username,
                'remember_me': False
            }
            yield scrapy.Request(
                url=self._track_url.format('login_ticket'),
                callback=self._login_global,
                method='POST',
                headers=self._headers,
                body=json.dumps(self._login_data)
            )
        else:
            # Username, password or section nzz.at not found in feeds.cfg.
            self.logger.error('Login failed: No username or password given')

    def _login_global(self, response):
        login_ticket = json.loads(response.text)['data']['login_ticket']
        self._login_data.update({
            'login_ticket': login_ticket,
            'service': 'nzzat',
            'service_id': 'nzzat',
        })
        yield scrapy.Request(
            url=self._track_url.format('login'),
            callback=self._login_local,
            method='POST',
            headers=self._headers,
            body=json.dumps(self._login_data)
        )

    def _login_local(self, response):
        service_ticket = json.loads(response.text)['service_ticket']
        self._login_data = {
            'service_ticket': service_ticket,
            'service': 'nzzat',
            'service_id': 'nzzat',
            'remember_me': False,
        }
        yield scrapy.Request(
            url=self._login_url.format('servicesession'),
            callback=self._after_login,
            method='POST',
            headers=self._headers,
            body=json.dumps(self._login_data)
        )

    def _after_login(self, response):
        yield scrapy.Request('https://nzz.at', self._parse_menu)

    def _parse_menu(self, response):
        for url in response.css(
                '.c-menu--main .c-menu__link::attr(href)').extract():
            yield scrapy.Request(url, self._parse_ressort)

    def _parse_ressort(self, response):
        for url in response.css(
                '.teaser__text .teaser__wrapper::attr(href)').extract()[
                    :self._max_items]:
            yield scrapy.Request(url, self._parse_article)

    def _parse_article(self, response):
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='https://{}'.format(self.name))
        il.add_css('link', '.c-input--share::attr(value)')
        il.add_css('author_name', '.hero--inner-meta__author::text',
                   re='von (.*)')
        il.add_css('title', '.hero--inner-meta__header::text')
        il.add_css('title', 'h1::text')
        il.add_css('updated', '.hero--inner-meta__date::text')
        il.add_value('content_html', '<img src="{}">'.format(
            response.xpath('//meta[@itemprop="image"]/@content').
            extract_first())
        )
        il.add_css('content_html', '.o-post')
        for category in response.css(
                '.o-path-inner ul li a::text').extract()[1:]:
            il.add_value('category', category)
        il.add_css('category', '.hero--inner-meta__term::text')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
