import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class OpenwrtOrgSpider(FeedsSpider):
    name = "openwrt.org"
    allowed_domains = ["openwrt.org"]
    start_urls = ["https://openwrt.org/releases/start"]

    feed_title = "New OpenWrt Release Builds"
    feed_subtitle = "Newest release builds from OpenWrt."
    feed_link = f"https://{name}"
    feed_icon = f"{feed_link}/lib/tpl/openwrt/images/apple-touch-icon.png"
    feed_logo = f"{feed_link}/lib/tpl/openwrt/images/logo.png"

    def parse(self, response):
        # Page with all major releases
        xpath = '//div[@class="page group"]//a[contains(@href, "/start")]/@href'
        for href in response.xpath(xpath).extract():
            yield scrapy.Request(
                response.urljoin(href), self.parse_release, meta={"dont_cache": True}
            )

    def parse_release(self, response):
        # All minor releases per major release
        xpath = '//a[contains(@href, "notes")][text()="Release Notes"]/@href'
        for href in response.xpath(xpath):
            url = f"{self.feed_link}/{href.extract().lstrip('/')}"
            yield scrapy.Request(url, self.parse_release_notes)

    def parse_release_notes(self, response):
        il = FeedEntryItemLoader(
            response=response,
            timezone="Europe/Berlin",
            base_url=self.feed_link,
            remove_elems=[".cookielaw-banner"],
        )
        il.add_xpath("title", "//h1/text()")
        il.add_value("link", response.url)
        il.add_xpath("updated", '//div[@class="docInfo"]', re="Last modified: (.*) by")
        il.add_value("content_html", "<h1>Release Notes</h1>")
        il.add_xpath("content_html", "//h1/following-sibling::*")
        return il.load_item()
