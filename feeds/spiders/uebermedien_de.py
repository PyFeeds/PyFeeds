import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class UebermedienDeSpider(FeedsXMLFeedSpider):
    name = 'uebermedien.de'
    allowed_domains = ['uebermedien.de']
    start_urls = ['https://uebermedien.de/feed/']
    namespaces = [('dc', 'http://purl.org/dc/elements/1.1/')]

    _title = 'uebermedien.de'
    _subtitle = 'Medien besser kritisieren.'

    def parse_node(self, response, node):
        il = FeedEntryItemLoader(response=response,
                                 base_url='http://{}'.format(self.name),
                                 dayfirst=True)
        il.add_xpath('updated', '//pubDate/text()')
        il.add_value('author_name',
                     node.xpath('//dc:creator/text()').extract_first())
        il.add_xpath('category', '//category/text()')
        title = node.xpath('(//title)[2]/text()').extract()
        if not title:
            # Fallback to the first category if no title is provided
            # (e.g. comic).
            title = response.xpath('//category/text()').extract_first()
        il.add_value('title', title)
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
