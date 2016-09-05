# -*- coding: utf-8 -*-

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class HelpGvAtSpider(FeedsSpider):
    name = 'help.gv.at'
    allowed_domains = [name]
    start_urls = ['https://www.{}/Portal.Node/hlpd/public'.format(name)]

    _title = 'HELP.gv.at'
    _subtitle = 'Ihr Wegweiser durch die Behörden und Ämter in Österreich'
    _link = 'https://www.{}'.format(name)
    _icon = 'https://www.{}/HLPD_Static/img/favicon.ico'.format(name)
    _logo = ('https://www.{}/HLPD_Static/img/'
             '120924_Header_helpgv_links.jpg'.format(name))
    _timezone = 'Europe/Vienna'

    def parse(self, response):
        yield scrapy.Request(
            'https://www.{}/Portal.Node/hlpd/public/content/171/'
            'Seite.1710000.html'.format(self.name), self._parse_lists)

        yield scrapy.Request(
            'https://www.{}/Portal.Node/hlpd/public/content/194/'
            'Seite.1940000.html'.format(self.name), self._parse_lists)

        for link in response.css('.Aktuelles a::attr(href)').extract():
            yield scrapy.Request(response.urljoin(link), self._parse_item)

    def _parse_lists(self, response):
        for link in response.css('.Content ul a::attr(href)').extract():
            yield scrapy.Request(response.urljoin(link), self._parse_item)

    def _parse_item(self, response):
        remove_elems = [
            'h1', '.nono', '.acceptance_org', '.state', 'script',
            '.gentics-portletreload-position-notvisibleposition'
        ]
        remove_elems_xpath = [
            """
            //div[
                @class='advice' and
                child::div[@class='advice_text' and (
                    contains(., 'nicht die aktuelle Rechtslage') or
                    contains(., 'wird nicht laufend aktualisiert') or
                    contains(., 'Übersicht über bisherige "Themen des Monats"')
                )]
            ]
            """,
            # Remove table of contents.
            "//li[child::a[starts-with(@href, '#')]]",
            "//ul[not(li)]",
        ]
        change_tags = {
            'abbr': 'span',
        }
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='https://www.{}'.format(self.name),
                                 remove_elems=remove_elems,
                                 remove_elems_xpath=remove_elems_xpath,
                                 change_tags=change_tags,
                                 dayfirst=True)
        il.add_value('link', response.url)
        il.add_xpath(
            'author_name',
            '//div[@class="acceptance_org"]/text()[preceding-sibling::br]',
        )
        il.add_xpath('title', '//meta[@name="og:title"]/@content')
        il.add_value('updated',
                     response.css('.state').re_first(r'(\d{2}\.\d{2}\.\d{4})'))
        il.add_css('content_html', '.Content')
        yield il.load_item()
