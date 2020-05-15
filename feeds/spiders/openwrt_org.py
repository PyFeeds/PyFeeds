import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class OpenwrtOrgSpider(FeedsSpider):
    name = "openwrt.org"
    allowed_domains = ["openwrt.org"]
    start_urls = ["https://openwrt.org/releases/start"]

    feed_title = ("New OpenWrt Release Builds",)
    feed_subtitle = "Newest release builds from OpenWrt."
    _base_url = "https://{}".format(name)
    feed_icon = "https://{}/lib/tpl/openwrt/images/apple-touch-icon.png".format(name)
    feed_logo = "https://{}/lib/tpl/openwrt/images/logo.png".format(name)

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
            url = "/".join((self._base_url, href.extract().lstrip("/")))
            yield scrapy.Request(url, self.parse_release_notes)

    def parse_release_notes(self, response):
        il = FeedEntryItemLoader(
            response=response, timezone="Europe/Berlin", base_url=self._base_url
        )
        il.add_xpath("title", "//h1/text()")
        il.add_value("link", response.url)
        il.add_xpath("updated", '//div[@class="docInfo"]', re="Last modified: (.*) by")
        il.add_value("content_html", "<h1>Release Notes</h1>")
        il.add_xpath("content_html", "//h1/following-sibling::*")
        return scrapy.Request(
            response.url.replace("notes-", "changelog-"),
            self.parse_release_changelog,
            meta={"il": il},
        )

    def parse_release_changelog(self, response):
        il = FeedEntryItemLoader(
            response=response, parent=response.meta["il"], base_url=self._base_url
        )
        il.add_value("content_html", "<h1>Detailed Changelog</h1>")
        il.add_xpath("content_html", "//h1/following-sibling::*")
        return il.load_item()
