from datetime import timedelta

import delorean
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class ProfilAtSpider(FeedsSpider):
    name = 'profil.at'
    allowed_domains = ['profil.at']

    _title = 'PROFIL'
    _subtitle = 'Österreichs unabhängiges Nachrichtenmagazin'
    _timezone = 'Europe/Vienna'
    # Parse articles from the last 3 days that have content.
    _max_days = 3
    # Don't try more than 14 days for content.
    _max_days_limit = 14

    def build_request(self, day, max_days, max_days_limit):
        return scrapy.Request(
            'https://www.{}/archiv/{}'.format(
                self.name,
                day.shift(self._timezone).format_datetime('Y/M/d')),
            self.parse_archive_page,
            meta={'handle_httpstatus_list': [404],
                  'day': day,
                  'max_days': max_days,
                  'max_days_limit': max_days_limit})

    def start_requests(self):
        yield self.build_request(delorean.utcnow(), self._max_days,
                                 self._max_days_limit)

    def parse_archive_page(self, response):
        day = response.meta['day'] - timedelta(days=1)
        max_days_limit = response.meta['max_days_limit'] - 1
        max_days = response.meta['max_days']

        if response.status == 200:
            for link in response.xpath('//h1/a/@href').extract():
                yield scrapy.Request(response.urljoin(link), self.parse_item)
            max_days -= 1

        if max_days > 0 and max_days_limit > 0:
            yield self.build_request(day, max_days, max_days_limit)

    def parse_item(self, response):
        remove_elems = [
            'aside', 'script', 'h1', '.breadcrumbs', '.author-date',
            '.artikel-social-kommentar', '.bild-copyright',
            '.ressortTitleMobile', '.article-number', '.artikel-kommentarlink'
        ]
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='http://{}'.format(self.name),
                                 remove_elems=remove_elems)
        il.add_value('link', response.url)
        il.add_xpath('author_name', '//a[@rel="author"]/text()')
        il.add_xpath(
            'author_name', 'substring-before(substring-after('
            '(//section[@class="author-date"]/text())[1]'
            ', "Von"), "(")')
        il.add_value('author_name', 'Red.')
        il.add_xpath('title', '//h1/text()')
        il.add_xpath(
            'updated', 'substring-before('
            '//meta[@property="article:published_time"]/@content'
            ', "+")')
        il.add_xpath('content_html', '//article')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
