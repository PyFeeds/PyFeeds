#!/usr/bin/python3

from datetime import timedelta
import json

from scrapy import Request
import delorean

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class TvthekOrfAtSpider(FeedsSpider):
    name = 'tvthek.orf.at'
    allowed_domains = ['tvthek.orf.at']

    _title = 'TVthek.ORF.at'
    _subtitle = 'ORF TVTHEK'
    _link = 'http://tvthek.orf.at'
    _timezone = 'Europe/Vienna'
    _token = '027f84a09ec56b'

    def start_requests(self):
        # We only parse today and yesterday because at the end of the day this
        # already produces a lot of requests and feed readers cache previous
        # days (i.e. old contents of our feed) anyways.
        # It's not enough to parse only today because we might miss shows that
        # aired just before midnight but were streamed after midnight
        # (see also https://github.com/nblock/feeds/issues/27)
        today = delorean.utcnow().shift(self._timezone)
        for day in [today, today - timedelta(days=1)]:
            yield Request('http://{}/service_api/token/{}/episodes/by_date/{}'.
                          format(self.name, self._token,
                                 day.format_datetime('YMMdd')))

    def parse(self, response):
        json_response = json.loads(response.body_as_unicode())
        if 'nextPage' in json_response['paginationMetaData']:
            yield Request(json_response['paginationMetaData']['nextPage'])

        for item in json_response['episodeShorts']:
            yield Request(item['detailApiCall'], self.parse_item_details)

    def parse_item_details(self, response):
        item = json.loads(response.body_as_unicode())['episodeDetail']
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 dayfirst=True)
        self.logger.info('Episode name: {}, program name: {}'.format(
            item['title'], item['program']['name']))
        il.add_value('title', item['title'])
        text = item['descriptions'][0]['text']
        if text:
            il.add_value('content_html', text.replace('\r\n', '<br>'))
        # WARNING: The API uses multiple datetime formats, depending on the
        # field. You might need to adjust dayfirst if you change the field.
        il.add_value('updated', item['date'])
        il.add_value('category', self._categories_from_oewa_base_path(
                     item['oewaBasePath']))
        # The "id"s are bogus values because we don't know the actual values
        # for the URL. We make another request to see where we get redirected.
        yield Request('http://{}/program/id/{}/id/{}'.format(
            self.name, item['program']['programId'], item['episodeId']),
            self.parse_item_link, meta={'dont_redirect': True, 'item': il,
                                        'handle_httpstatus_list': [301]})

    def parse_item_link(self, response):
        il = response.meta['item']
        il.add_value('link', response.headers['Location'].decode('ascii'))
        yield il.load_item()

    def _categories_from_oewa_base_path(self, oewa_base_path):
        """Parse ÖWA Base Path into a list of categories.

         Base paths look like this:

           * RedCont/KulturUndFreizeit/FilmUndKino
           * RedCont/KulturUndFreizeit/Sonstiges
           * RedCont/Lifestyle/EssenUndTrinken
           * RedCont/Nachrichten/Nachrichtenueberblick
           * RedCont/Sport/Sonstiges
        """
        old_new = {
            'RedCont': '', 'Sonstiges': '', 'Und': ' und ',
            'ue': 'ü', 'ae': 'ä', 'oe': 'ö',
            'Ue': 'Ü', 'Ae': 'Ä', 'Oe': 'Ö'
        }
        for old, new in old_new.items():
            oewa_base_path = oewa_base_path.replace(old, new)
        return filter(lambda x: x != '', oewa_base_path.split('/'))


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
