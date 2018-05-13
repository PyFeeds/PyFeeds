import datetime

import scrapy
import w3lib

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class AkCiandoComSpider(FeedsSpider):
    name = "ak.ciando.com"
    allowed_domains = ["ak.ciando.com"]
    start_urls = [
        "http://ak.ciando.com/shop/index.cfm?fuseaction=cat_overview&cat_ID=0"
        "&cat_nav=0&more_new=1&rows=100&intStartRow=1"
    ]

    _title = "AK Digitale Bibliothek"
    _subtitle = "Neue Titel in der digitalen AK Bibliothek"

    def parse(self, response):
        for link in response.xpath('//p[@class="p_blr_title"]//a/@href').extract():
            yield scrapy.Request(response.urljoin(link), self.parse_item)

    def parse_item(self, response):
        il = FeedEntryItemLoader(
            selector=response.xpath('//div[@id="maincontentbook"]')
        )
        il.add_xpath("title", '//h1[@class="p_book_title"]/text()')
        il.add_xpath("title", '//h3[@class="p_book_title_ebook"]/text()')
        il.add_value("link", response.url)
        il.add_value("author_name", self._title)
        il.add_xpath("content_html", '//h1[@class="p_book_title"]/text()')
        il.add_xpath("content_html", '//h2[@class="p_book_author"]/text()')
        il.add_xpath("content_html", '//p[@class="p_book_publisher"]/text()')
        il.add_xpath("content_html", '//p[@class="p_book_isbn"]/text()')
        il.add_xpath("content_html", '(//span[@class="txt10px"])[1]/text()')
        il.add_xpath("content_html", '(//span[@class="txt10px"])[3]/text()')
        il.add_xpath("content_html", '//div[@class="bookcontent"]//text()')
        il.add_xpath("content_html", '//div[@class="p_book_image"]/img')
        il.add_xpath("content_html", '//span[@style="color:red;"]/b/text()')

        # NOTE: The page does not provide any usable timestamp so we convert
        # the bok_id parameter to unix epoch.
        bok_id = w3lib.url.url_query_parameter(response.url, "bok_id", "0")
        timestamp = datetime.datetime.utcfromtimestamp(int(bok_id))
        il.add_value("updated", timestamp.isoformat())

        yield il.load_item()


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
