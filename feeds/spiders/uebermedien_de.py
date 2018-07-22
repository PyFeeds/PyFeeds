import json
from collections import OrderedDict
from urllib.parse import parse_qs, urlparse

import scrapy
from scrapy.http import FormRequest

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class UebermedienDeSpider(FeedsXMLFeedSpider):
    name = "uebermedien.de"
    allowed_domains = ["uebermedien.de", "steadyhq.com"]
    start_urls = ["https://uebermedien.de/feed/"]
    namespaces = [("dc", "http://purl.org/dc/elements/1.1/")]

    _title = "uebermedien.de"
    _subtitle = "Medien besser kritisieren."
    _steady_token = None

    def start_requests(self):
        username = self.spider_settings.get("username")
        password = self.spider_settings.get("password")
        if username and password:
            yield scrapy.Request(
                "https://steadyhq.com/en/oauth/authorize?"
                + "client_id=0c29f006-1a98-48f1-8a63-2c0652c59f28&"
                + "redirect_uri=https://uebermedien.de&scope=read&"
                + "response_type=code&refresh_only=false",
                callback=self._steady_login,
            )
        else:
            self.logger.info("Login failed: No username or password given")
            # We can still try to scrape the free articles.
            yield from super().start_requests()

    def _steady_login(self, response):
        username = self.spider_settings.get("username")
        password = self.spider_settings.get("password")
        yield FormRequest.from_response(
            response,
            formdata={"user[email]": username, "user[password]": password},
            callback=self._request_steady_token,
            dont_filter=True,
            meta={"handle_httpstatus_list": [301]},
        )

    def _request_steady_token(self, response):
        try:
            code = parse_qs(urlparse(response.url).query)["code"][0]
        except KeyError:
            self.logger.error("Login failed: Wrong username and password")
            return

        body = OrderedDict([
            ("client_id", "0c29f006-1a98-48f1-8a63-2c0652c59f28"),
            ("grant_type", "authorization_code"),
            ("code", code),
            ("redirect_uri", "https://uebermedien.de"),
        ])
        yield scrapy.Request(
            "https://steadyhq.com/api/v1/oauth/token",
            method="POST",
            body=json.dumps(body),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            callback=self._set_steady_token,
        )

    def _set_steady_token(self, response):
        self._steady_token = json.loads(response.text)["access_token"]
        return super().start_requests()

    def parse_node(self, response, node):
        il = FeedEntryItemLoader(
            response=response, base_url="http://{}".format(self.name), dayfirst=True
        )
        il.add_value("updated", node.xpath("//pubDate/text()").extract_first())
        il.add_value("author_name", node.xpath("//dc:creator/text()").extract_first())
        il.add_value("category", node.xpath("//category/text()").extract())
        title = node.xpath("(//title)[2]/text()").extract()
        if not title:
            # Fallback to the first category if no title is provided
            # (e.g. comic).
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
        remove_elems = ["iframe", "script"]
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=remove_elems,
            base_url="http://{}".format(self.name),
        )
        il.add_css("content_html", ".entry-content")
        return il.load_item()
