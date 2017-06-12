import json

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class Oe1OrfAtSpider(FeedsSpider):
    name = 'oe1.orf.at'
    allowed_domains = ['audioapi.orf.at']
    start_urls = ['https://audioapi.orf.at/oe1/api/json/current/broadcasts']

    _title = 'oe1.ORF.at'
    _subtitle = 'Ö1 Webradio'
    _link = 'http://oe1.orf.at'
    _timezone = 'Europe/Vienna'

    def parse(self, response):
        for day in json.loads(response.text)[-2:]:
            for broadcast in day['broadcasts']:
                # Only parse if already recorded (i.e. not live/in the future).
                if broadcast['state'] == 'C':
                    yield scrapy.Request(broadcast['href'],
                                         self.parse_broadcast,
                                         meta={'oe1_day': day['day']})

    def parse_broadcast(self, response):
        broadcast = json.loads(response.text)
        il = FeedEntryItemLoader(response=response, timezone=self._timezone,
                                 dayfirst=False)
        link = 'https://{}/programm/{}/{}'.format(
            self.name, response.meta['oe1_day'], broadcast['programKey'])
        il.add_value('link', link)
        il.add_value('title', broadcast['title'])
        if broadcast.get('streams'):
            stream = 'http://loopstream01.apa.at/?channel=oe1&id={}'.format(
                broadcast['streams'][0]['loopStreamId'])
            il.add_value('enclosure_iri', stream)
            il.add_value('enclosure_type', 'audio/mpeg')
        il.add_value('updated', broadcast['niceTimeISO'])
        if broadcast['subtitle']:
            il.add_value('content_html', '<strong>{}</strong>'.format(
                broadcast['subtitle']))
        for item in broadcast['items']:
            if 'title' in item:
                il.add_value('content_html',
                             '<h3>{}</h3>'.format(item['title']))
            il.add_value('content_html', item.get('description'))
        il.add_value('content_html', broadcast['description'])
        yield il.load_item()
