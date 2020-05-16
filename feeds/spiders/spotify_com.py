import json

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class SpotifyComSpider(FeedsSpider):
    name = "spotify.com"

    def start_requests(self):
        self._shows = self.settings.get("FEEDS_SPIDER_SPOTIFY_COM_SHOWS")
        if self._shows:
            self._shows = set(self._shows.split())
        else:
            self.logger.error("No shows given!")
            return

        self._market = self.settings.get("FEEDS_SPIDER_SPOTIFY_COM_MARKET")
        if not self._market:
            self.logger.error("Please specify a market (country code) in the config!")
            return

        yield scrapy.Request(
            "https://open.spotify.com/get_access_token?"
            + "reason=transport&productType=web_player",
            meta={"dont_cache": True},  # Only valid for a very short time.
        )

    def parse(self, response):
        response = json.loads(response.text)
        access_token = response["accessToken"]
        for show in self._shows:
            yield scrapy.Request(
                f"https://api.spotify.com/v1/shows/{show}?market={self._market}",
                self._parse_show,
                meta={"spotify_show": show, "dont_cache": True},
                headers={"Authorization": f"Bearer {access_token}"},
            )

    def feed_headers(self):
        return []

    def _parse_show(self, response):
        result = json.loads(response.text)

        yield generate_feed_header(
            title=result["name"],
            link=result["external_urls"]["spotify"],
            icon=result["images"][-1]["url"],
            logo=result["images"][0]["url"],
            path=response.meta["spotify_show"],
        )

        for episode in result["episodes"]["items"]:
            il = FeedEntryItemLoader()
            il.add_value("link", episode["external_urls"]["spotify"])
            il.add_value("updated", episode["release_date"])
            il.add_value("title", episode["name"])
            il.add_value("content_html", episode["description"])
            il.add_value("path", response.meta["spotify_show"])
            yield il.load_item()
