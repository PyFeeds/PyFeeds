import json
from datetime import datetime

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class ViceComSpider(FeedsSpider):
    name = "vice.com"

    def feed_headers(self):
        if not self._locales:
            return []

        for locale in self._locales:
            yield generate_feed_header(
                title="VICE {}".format(locale.title()),
                path=locale,
                link="https://www.{}".format(self.name),
                logo="https://www.{}/favicons/"
                "apple-touch-icon-60x60.png".format(self.name),
                icon="https://www.{}/favicons/"
                "apple-touch-icon-60x60.png".format(self.name),
            )

    def start_requests(self):
        self._locales = self.settings.get("FEEDS_SPIDER_VICE_COM_LOCALES")
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
        remove_elems = [
            "hr + p",
            "hr",
            "iframe",
            "p i:last-of-type:contains('Facebook'):contains('Twitter')",
        ]
        for article in articles:
            il = FeedEntryItemLoader(timezone="UTC", remove_elems=remove_elems)
            il.add_value("title", article["title"])
            link = article["url"]
            if not link:
                link = "https://www.vice.com/{locale}/article/{web_id}/{slug}".format(
                    locale=response.meta["locale"],
                    web_id=article["web_id"],
                    slug=article["slug"],
                )
            il.add_value("link", link)
            if "thumbnail_url_1_1" in article:
                il.add_value(
                    "content_html",
                    '<img src="{}">'.format(article["thumbnail_url_1_1"]),
                )
            il.add_value("content_html", article["body"])
            il.add_value(
                "updated", datetime.utcfromtimestamp(article["publish_date"] / 1000)
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
