#!/usr/bin/python3

from scrapy.http import HtmlResponse
from scrapy.spiders import Spider
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.loaders import FeedItemLoader


class WienerLinienAtSpider(Spider):
    name = 'wienerlinien.at'
    allowed_domains = ['wienerlinien.at']
    custom_settings = {
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html',
            # Don't include Accept-Language so the datetime in the HTML
            # response includes the time.
        }
    }
    start_urls = [
        'http://www.wienerlinien.at/eportal3/ep/scrollingListView.do?'
        'scrolling=true&startIndex=0&channelId=-47186&programId=74577'
    ]

    _timezone = 'Europe/Vienna'

    def parse(self, response):
        il = FeedItemLoader()
        il.add_value('title', 'Wiener Linien')
        il.add_value('subtitle', 'Aktuelle Meldungen')
        il.add_value('link', 'http://wienerlinien.at')
        il.add_value('author_name', self.name)
        yield il.load_item()

        # Wiener Linien returns HTML with an XML content type which creates an
        # XmlResponse.
        response = HtmlResponse(url=response.url, body=response.body)
        for item in response.css('.block-news-item'):
            il = FeedEntryItemLoader(response=response,
                                     timezone=self._timezone,
                                     base_url='http://{}'.format(self.name))
            link = response.urljoin(item.css('a::attr(href)').extract_first())
            il.add_value('link', link)
            il.add_value('title', item.css('h3::text').extract_first())
            il.add_value('updated', item.css('.date::text').extract_first())
            yield scrapy.Request(link, self.parse_item, meta={'il': il})

    def parse_item(self, response):
        remove_elems = ['h1', '.delayed-image-load']
        change_tags = {'noscript': 'div'}
        il = FeedEntryItemLoader(response=response,
                                 parent=response.meta['il'],
                                 remove_elems=remove_elems,
                                 change_tags=change_tags,
                                 base_url='http://{}'.format(self.name))
        il.add_xpath('content_html', '//div[@id="main-inner"]')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
