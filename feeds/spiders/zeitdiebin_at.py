import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class ZeitdiebinAtSpider(FeedsSpider):
    name = "zeit.diebin.at"
    allowed_domains = ["zeit.diebin.at"]
    start_urls = ["https://zeit.diebin.at/upcoming"]

    _title = "zeitdiebin"
    _subtitle = "irgendwas ist immer ..."
    _link = "https://{}".format(name)
    _logo = "https://{}/favicon.ico".format(name)
    _timezone = "Europe/Vienna"

    def parse(self, response):
        for link in response.css("a[href*=events]::attr(href)").re(r"events/\d+"):
            yield scrapy.Request(response.urljoin(link), self.parse_item)

    def parse_item(self, response):
        il = FeedEntryItemLoader(
            response=response,
            base_url="{}/".format(self._link),
            timezone=self._timezone,
            dayfirst=True,
            remove_elems=[".ruler", "h1"],
        )
        il.add_css("title", "h1.event-title::text")
        il.add_value("link", response.url)
        il.add_css("content_html", "div#content.container")
        yield il.load_item()
