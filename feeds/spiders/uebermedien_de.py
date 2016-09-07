
import html

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders.blendle import BlendleSession, BlendleAuthenticationError
from feeds.spiders import FeedsXMLFeedSpider


class UebermedienDeSpider(FeedsXMLFeedSpider):
    name = 'uebermedien.de'
    allowed_domains = ['uebermedien.de']
    start_urls = ['http://www.uebermedien.de/feed/']
    namespaces = [('dc', 'http://purl.org/dc/elements/1.1/')]

    _title = 'uebermedien.de'
    _subtitle = 'Medien besser kritisieren.'

    def parse(self, response):
        # Try to login to Blendle.
        self._blendle_session = BlendleSession(spider=self,
                                               provider='uebermedien')
        try:
            # Continue with parsing the feed after trying to log in.
            yield self._blendle_session.login(
                callback=(
                    # Continue with parsing the feed after logging in.
                    lambda: super(UebermedienDeSpider, self).parse(response)
                )
            )
        except BlendleAuthenticationError as ex:
            # No username or password given.
            self.logger.info(str(ex))
            yield from super().parse(response)

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
        if response.css('.entry_blendle_text'):
            self.logger.debug('Article {} is paywalled'.format(response.url))
            response.meta['il'].add_value('category', 'paywalled')
            callback_url = response.css(
                '.pwb-item::attr(data-purchase-callback-url)').extract_first()
            item_jwt = (
                response.css('.pwb-item::attr(data-item-jwt)').extract_first()
            )
            return self._blendle_session.parse_article(
                response=response, item_jwt=item_jwt,
                callback_url=callback_url,
                callback=self._parse_article_text)
        else:
            # Not paywalled.
            return self._parse_article_text(response)

    def _parse_article_text(self, response):
        remove_elems = ['iframe', '.blendlebutton__hide__post', '.pwb-item',
                        '.uebermedien_slogan', '.pwb-subscription']
        il = FeedEntryItemLoader(response=response,
                                 parent=response.meta['il'],
                                 remove_elems=remove_elems,
                                 base_url='http://{}'.format(self.name))
        il.add_css('content_html', '.entry-content')
        return il.load_item()
