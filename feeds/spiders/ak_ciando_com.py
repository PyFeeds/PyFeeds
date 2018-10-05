import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class AkCiandoComSpider(FeedsSpider):
    name = "ak.ciando.com"
    start_urls = [
        "https://ak.ciando.com/shop/index.cfm?fuseaction=cat_overview&cat_ID=0"
        "&cat_nav=0&more_new=1&rows=100&intStartRow=1"
    ]

    feed_title = "AK Digitale Bibliothek"
    feed_subtitle = "Neue Titel in der digitalen AK Bibliothek"
    feed_link = "https://{}".format(name)

    def parse(self, response):
        for link in response.xpath('//p[@class="p_blr_title"]//a/@href').extract():
            yield scrapy.Request(response.urljoin(link), self.parse_item)

    def parse_item(self, response):
        il = FeedEntryItemLoader(
            selector=response.xpath('//div[@id="maincontentbook"]'),
            base_url=self.feed_link,
        )
        il.add_xpath("title", '//h1[@class="p_book_title"]/text()')
        il.add_xpath("title", '//h3[@class="p_book_title_ebook"]/text()')
        il.add_value("link", response.url)
        il.add_value("author_name", self.feed_title)
        il.add_xpath("content_html", '//h1[@class="p_book_title"]/text()')
        il.add_xpath("content_html", '//h2[@class="p_book_author"]/text()')
        il.add_xpath("content_html", '//p[@class="p_book_publisher"]/text()')
        il.add_xpath("content_html", '//p[@class="p_book_isbn"]/text()')
        il.add_xpath("content_html", '(//span[@class="txt10px"])[1]/text()')
        il.add_xpath("content_html", '(//span[@class="txt10px"])[3]/text()')
        il.add_xpath("content_html", '//div[@class="bookcontent"]//text()')
        il.add_xpath("content_html", '//div[@class="p_book_image"]/img')
        il.add_xpath("content_html", '//span[@style="color:red;"]/b/text()')
        return il.load_item()
