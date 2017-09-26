import html

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class UebermedienDeSpider(FeedsXMLFeedSpider):
    name = 'uebermedien.de'
    allowed_domains = ['uebermedien.de']
    start_urls = ['http://www.uebermedien.de/feed/']
    namespaces = [('dc', 'http://purl.org/dc/elements/1.1/')]

    _title = 'uebermedien.de'
    _subtitle = 'Medien besser kritisieren.'

    def parse_node(self, response, node):
        il = FeedEntryItemLoader(response=response,
                                 base_url='http://{}'.format(self.name),
                                 dayfirst=True)
        il.add_value('updated', node.xpath('//pubDate/text()').extract_first())
        il.add_value('author_name',
                     html.unescape(node.xpath('//dc:creator/text()').
                                   extract_first()))
        categories = node.xpath('//category/text()').extract()
        for category in categories:
            il.add_value('category', html.unescape(category))
        title = node.xpath('(//title)[2]/text()').extract()
        if not title and categories:
            # Fallback to the first category if no title is provided
            # (e.g. comic).
            title = categories[0]
        il.add_value('title', html.unescape(title))
        link = node.xpath('(//link)[2]/text()').extract_first()
        il.add_value('link', link)
        return scrapy.Request(link, self._parse_article, meta={'il': il})

    def _parse_article(self, response):
        remove_elems = ['iframe', 'script']
        il = FeedEntryItemLoader(response=response,
                                 parent=response.meta['il'],
                                 remove_elems=remove_elems,
                                 base_url='http://{}'.format(self.name))
        il.add_css('content_html', '.entry-content')
        return il.load_item()
