from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsCrawlSpider


class CbirdAtSpider(FeedsCrawlSpider):
    name = "cbird.at"
    allowed_domains = ["cbird.at"]
    start_urls = ["https://cbird.at/hilfe/neu/", "https://cbird.at/impressum"]
    rules = (Rule(LinkExtractor(allow=(r"hilfe/neu/(\d+)",)), callback="parse_item"),)

    feed_title = "Neue cbird Versionen"
    feed_subtitle = "Die neuesten Versionen von cbird."
    feed_link = start_urls[0]
    feed_icon = "https://{}/images/bird-1.png".format(name)
    feed_logo = "https://{}/images/bird-1.png".format(name)

    def parse_item(self, response):
        il = FeedEntryItemLoader(
            selector=response.xpath('//div[@class="main"]'), timezone="Europe/Vienna"
        )
        il.add_xpath("title", "h1/text()")
        il.add_value("link", response.url)
        il.add_xpath("content_html", "h1/following-sibling::*")
        il.add_value("updated", response.url.rstrip("/").split("/")[-1].split("_")[0])
        il.add_value("author_name", self.name)
        return il.load_item()

    def parse_imprint(self, response):
        self._author_name = (
            response.xpath('//div[@class="main"]/p/text()').re_first("Firma (.*)")
            or self.name
        )
