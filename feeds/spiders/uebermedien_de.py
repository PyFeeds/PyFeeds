import json
from collections import OrderedDict
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import scrapy
from inline_requests import inline_requests
from scrapy.http import FormRequest

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class UebermedienDeSpider(FeedsXMLFeedSpider):
    name = "uebermedien.de"
    start_urls = ["https://uebermedien.de/feed/"]
    namespaces = [("dc", "http://purl.org/dc/elements/1.1/")]
    custom_settings = {"COOKIES_ENABLED": True}

    feed_title = "uebermedien.de"
    feed_subtitle = "Medien besser kritisieren."
    _steady_token = None

    def start_requests(self):
        self._username = self.settings.get("FEEDS_SPIDER_UEBERMEDIEN_DE_USERNAME")
        self._password = self.settings.get("FEEDS_SPIDER_UEBERMEDIEN_DE_PASSWORD")
        if self._username and self._password:
            yield from self._steady_login(None)
        else:
            # We can still try to scrape the free articles.
            self.logger.info("Login failed: No username or password given")

        yield from super().start_requests()

    @inline_requests
    def _steady_login(self, response):
        response = yield scrapy.Request(
            "https://steadyhq.com/oauth/authorize?"
            + "client_id=0c29f006-1a98-48f1-8a63-2c0652c59f28&"
            + "redirect_uri=https://uebermedien.de&scope=read&"
            + "response_type=code&refresh_only=false",
            meta={"cache_expires": timedelta(days=1)},
        )

        response = yield FormRequest.from_response(
            response,
            formdata=OrderedDict(
                [("user[email]", self._username), ("user[password]", self._password)]
            ),
            dont_filter=True,
            meta={"handle_httpstatus_list": [301], "cache_expires": timedelta(days=1)},
        )

        try:
            code = parse_qs(urlparse(response.url).query)["code"][0]
        except KeyError:
            self.logger.error("Login failed: Wrong username and password")
            return

        body = OrderedDict(
            [
                ("client_id", "0c29f006-1a98-48f1-8a63-2c0652c59f28"),
                ("grant_type", "authorization_code"),
                ("code", code),
                ("redirect_uri", "https://uebermedien.de"),
            ]
        )
        response = yield scrapy.Request(
            "https://steadyhq.com/api/v1/oauth/token",
            method="POST",
            body=json.dumps(body),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            meta={"cache_expires": timedelta(days=1)},
        )
        self._steady_token = json.loads(response.text)["access_token"]

    def parse_node(self, response, node):
        il = FeedEntryItemLoader(
            response=response, base_url="https://{}".format(self.name), dayfirst=True
        )
        il.add_value("updated", node.xpath("//pubDate/text()").extract_first())
        il.add_value("author_name", node.xpath("//dc:creator/text()").extract_first())
        il.add_value("category", node.xpath("//category/text()").extract())
        title = node.xpath("(//title)[2]/text()").extract()
        if not title:
            # Fallback to the first category if no title is provided (e.g. comic).
            title = node.xpath("//category/text()").extract_first()
        il.add_value("title", title)
        link = node.xpath("(//link)[2]/text()").extract_first()
        il.add_value("link", link)
        if self._steady_token:
            cookies = {"steady-token": self._steady_token}
        else:
            cookies = None
        return scrapy.Request(
            link, self._parse_article, cookies=cookies, meta={"il": il}
        )

    def _parse_article(self, response):
        remove_elems = ["script"]
        convert_footnotes = [".footnoteContent"]
        pullup_elems = {".footnoteContent": 1}
        change_tags = {".entry-content-info-box": "blockquote"}
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=remove_elems,
            change_tags=change_tags,
            base_url="https://{}".format(self.name),
            convert_footnotes=convert_footnotes,
            pullup_elems=pullup_elems,
        )
        il.add_css("content_html", ".entry-content")
        return il.load_item()
