from datetime import datetime
import json
import urllib.parse

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class NzzAtSpider(FeedsSpider):
    name = 'nzz.at'
    allowed_domains = ['nzz.at']
    start_urls = ['https://nzz.at/wp/wp-login.php']

    _title = 'NZZ.at'
    _subtitle = 'Hintergrund, Analyse, Kommentar'
    _link = 'https://nzz.at'
    _timezone = 'GMT'
    _excluded = []
    _max_items = 20
    _num_items = 0

    def parse(self, response):
        username = self.spider_settings.get('username')
        password = self.spider_settings.get('password')
        if username and password:
            yield scrapy.FormRequest.from_response(
                response,
                formname='loginform',
                formdata={'log': username,
                          'pwd': password,
                          'redirect_to': '/',
                          'testcookie': '1'},
                callback=self._after_login
            )
        else:
            # Username, password or section nzz.at not found in feeds.cfg.
            self.logger.error('Login failed: No username or password given')

    def _after_login(self, response):
        if 'FEHLER' in response.body_as_unicode():
            self.logger.error('Login failed: Username or password wrong')
            return
        url = response.css('.c-teaser--hero a').xpath('@href').extract_first()
        return scrapy.Request(url, callback=self._parse_ajax_url)

    def _parse_ajax_url(self, response):
        self.ajax_url = (
            response.selector.re('"ajaxurl":"([^"]+)"')[0].replace('\\', '')
        )
        yield scrapy.Request(self._next_url(), self.parse_item)

    def _next_url(self):
        params = [
            ('order', 'DESC'),
            ('orderby', 'date'),
            ('post_type', 'phenomenon'),
            ('date', str(datetime.utcnow().replace(microsecond=0))),
        ]
        for exclude in self._excluded:
            params.append(('excluded[]', exclude))
        params.append(('action', 'endless_scroll_phenomenon'))
        return self.ajax_url + '&' + urllib.parse.urlencode(params)

    def parse_item(self, response):
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='http://{}'.format(self.name),
                                 convert_footnotes=['.c-footnote__content'])
        article = json.loads(response.body_as_unicode())['data']
        il.add_value('link', article['shorturl'])
        il.add_value('title', article['overline'])
        il.add_value('title', article['post']['post_title'])
        il.add_value('content_html', article['reading_time'])
        il.add_value('content_html', '<hr>')
        il.add_value('content_html', article['post']['post_content'])
        il.add_value('author_name', article['author']['name'])
        il.add_value('updated', article['post']['post_modified_gmt'])
        if article['channel']:
            il.add_value('category', article['channel'])
        self._excluded.append(article['post']['ID'])
        self._num_items += 1
        yield il.load_item()

        if self._num_items < self._max_items:
            yield scrapy.Request(self._next_url(), self.parse_item)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
