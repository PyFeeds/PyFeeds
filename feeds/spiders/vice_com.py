import json
from datetime import datetime

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class ViceComSpider(FeedsSpider):
    name = "vice.com"
    allowed_domains = ["vice.com"]

    _title = "VICE"
    _link = "https://www.{}".format(name)
    _logo = "https://www.{}/favicons/apple-touch-icon-60x60.png".format(name)
    _icon = _logo
    _timezone = "Europe/Vienna"

    def feed_headers(self):
        if not self._locales:
            return []

        for locale in self._locales:
            yield self.generate_feed_header(
                title="{} {}".format(self._title, locale.title()), path=locale
            )

    def start_requests(self):
        self._locales = self.spider_settings.get("locales")
        if not self._locales:
            self.logger.error("Please specify locale(s) for vice.com in config file!")
            return

        self._locales = self._locales.split()

        for locale in self._locales:
            yield scrapy.Request(
                "https://www.{}/api/v1/articles?locale={}".format(self.name, locale),
                meta={"locale": locale, "dont_cache": True},
            )

    def parse(self, response):
        articles = json.loads(response.text)
        remove_elems = ["hr + p:contains('Auch bei Vice')", "hr", "iframe"]
        for article in articles:
            il = FeedEntryItemLoader(timezone=self._timezone, remove_elems=remove_elems)
            il.add_value("title", article["title"])
            il.add_value("link", article["url"])
            if "thumbnail_url_1_1" in article:
                il.add_value(
                    "content_html",
                    '<img src="{}">'.format(article["thumbnail_url_1_1"]),
                )
            il.add_value("content_html", article["body"])
            il.add_value(
                "updated", datetime.fromtimestamp(article["publish_date"] / 1000)
            )
            il.add_value(
                "author_name",
                [
                    contribution["contributor"]["full_name"]
                    for contribution in article["contributions"]
                ],
            )
            il.add_value("category", article["channel"]["name"])
            for topic in article["topics"] + [article["primary_topic"]]:
                if topic and "name" in topic:
                    il.add_value("category", topic["name"].title())
            if article["nsfw"]:
                il.add_value("category", "nsfw")
            if article["nsfb"]:
                il.add_value("category", "nsfb")
            il.add_value("path", response.meta["locale"])
            yield il.load_item()
