import json
import re
from datetime import timedelta

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

        user_agent = self.settings.get("USER_AGENT")

        yield scrapy.Request(
            "https://open.spotify.com",
            meta={
                "cache_expires": timedelta(hours=1),
                "handle_httpstatus_list": [302],
                "dont_redirect": True,
            },
            # Spotify checks the user agent and complains if it doesn't find a supported
            # browser.
            headers={"User-Agent": "{} Firefox/67.0".format(user_agent)},
        )

    def parse(self, response):
        access_token = None
        cookies = response.headers.getlist("Set-Cookie")
        for cookie in cookies:
            cookie = cookie.decode("ascii")
            if cookie.startswith("wp_access_token="):
                access_token = re.findall("wp_access_token=([^;]*)", cookie)[0]
                break

        for show in self._shows:
            yield scrapy.Request(
                "https://api.spotify.com/v1/shows/{}".format(show),
                self._parse_show,
                meta={"show": show, "dont_cache": True},
                headers={"Authorization": "Bearer {}".format(access_token)},
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
            path=response.meta["show"],
        )

        for episode in result["episodes"]["items"]:
            il = FeedEntryItemLoader()
            il.add_value("link", episode["external_urls"]["spotify"])
            il.add_value("updated", episode["release_date"])
            il.add_value("title", episode["name"])
            il.add_value("content_html", episode["description"])
            il.add_value("path", response.meta["show"])
            yield il.load_item()
