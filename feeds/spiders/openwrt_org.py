import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsCrawlSpider


class OpenwrtOrgSpider(FeedsCrawlSpider):
    name = "openwrt.org"
    allowed_domains = ["openwrt.org"]
    start_urls = ["https://openwrt.org/releases/start"]
    rules = (
        Rule(LinkExtractor(allow=("releases/(.*)/start",)), callback="parse_release"),
    )

    feed_title = ("New OpenWRT Release Builds",)
    feed_subtitle = "Newest release builds from OpenWRT."
    _base_url = "https://{}".format(name)
    feed_icon = "https://{}/lib/tpl/openwrt/images/apple-touch-icon.png".format(name)
    feed_logo = "https://{}/lib/tpl/openwrt/images/logo.png".format(name)

    def parse_release(self, response):
        for href in response.xpath(
            '//a[contains(@href, "notes")][text()="Release Notes"]/@href'
        ):
            prefix, latest = href.extract().split("-")
            major, minor, patch = latest.split(".")
            for m in range(int(patch), -1, -1):
                url = response.urljoin("{}-{}.{}.{}".format(prefix, major, minor, m))
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
