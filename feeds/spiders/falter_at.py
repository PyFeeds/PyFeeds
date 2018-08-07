import json
import re
from collections import OrderedDict
from datetime import timedelta

import scrapy
from dateutil.parser import parse as dateutil_parse

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class FalterAtSpider(FeedsSpider):
    name = "falter.at"
    # Don't overwhelm the poor Wordpress with too many requests at once.
    custom_settings = {"DOWNLOAD_DELAY": 1.0}

    _subtitle = "Wir holen dich da raus."
    _link = "https://www.falter.at"
    _timezone = "Europe/Vienna"

    def start_requests(self):
        pages = self.settings.get("FEEDS_SPIDER_FALTER_AT_PAGES")
        if pages:
            self.pages = pages.split()
        else:
            self.pages = ["wwei", "magazine"]

        if "magazine" in self.pages:
            abonr = self.settings.get("FEEDS_SPIDER_FALTER_AT_ABONR")
            password = self.settings.get("FEEDS_SPIDER_FALTER_AT_PASSWORD")
            if abonr and password:
                yield scrapy.FormRequest(
                    url="https://www.{}/falter/e-paper/login".format(self.name),
                    formdata={
                        "login[abonr]": abonr,
                        "login[password]": password,
                        "redirect_url": "/archiv/",
                    },
                    meta={
                        "dont_redirect": True,
                        "cache_expires": timedelta(days=1),
                        "handle_httpstatus_list": [302],
                    },
                    callback=self.request_archive,
                )
            else:
                # Username, password or section falter.at not found in feeds.cfg.
                self.logger.info(
                    "Login failed: No username or password given. "
                    + "Only free articles are available in full text."
                )
                yield self.request_archive()

        if "wwei" in self.pages:
            yield scrapy.Request(
                (
                    "https://wwei-api.{}/api/v1/simple_search?v=true&"
                    + "sort_pos=front&sort=review.post_date:desc&c=10"
                ).format(self.name),
                self.parse_wwei,
                meta={"dont_cache": True},
            )

    def request_archive(self, response=None):
        if response and response.status != 302:
            self.logger.error("Login failed: Username or password wrong!")
        else:
            return scrapy.Request(
                "https://www.{}/archiv/".format(self.name),
                self.parse_archive,
                meta={"dont_cache": True},
            )

    def feed_headers(self):
        for path in self.pages:
            yield self.generate_feed_header(path=path)

    def parse_wwei(self, response):
        entries = json.loads(response.text)[0]["hits"]
        for entry in entries:
            review = entry["review"]
            il = FeedEntryItemLoader(
                response=response,
                base_url="https://{}".format(self.name),
                timezone=self._timezone,
                dayfirst=False,
            )
            il.add_value("path", "wwei")
            il.add_value("title", review["post_title"])
            il.add_value("title", review["post_subtitle"])
            il.add_value("updated", review["post_date"])
            il.add_value(
                "link", "https://www.{}/lokal/{}".format(self.name, entry["id"])
            )
            il.add_value("author_name", review["meta"].split("|")[0].title())
            if "pictures" in entry and entry["pictures"]:
                il.add_value(
                    "content_html",
                    '<img src="https://fcc.at/ef/tmb200/{}">'.format(
                        entry["pictures"][0]["filename"]
                    ),
                )
            il.add_value("content_html", review["post_content"])
            yield il.load_item()

    def parse_archive(self, response):
        # The perks of having a JavaScript frontend ...
        revisions = json.loads(
            response.css(".content-main script ::text").re_first("revisions: (.*)"),
            object_pairs_hook=OrderedDict,
        )
        latest_issue_date = dateutil_parse(
            revisions.popitem(last=False)[1][-1], ignoretz=True
        )
        issuenr = latest_issue_date.strftime("%Y%W")
        yield scrapy.Request(
            response.urljoin(
                "/archiv/ajax/search?count=1000&issuenr={}".format(issuenr)
            ),
            self.parse_archive_search,
            meta={"issue_date": latest_issue_date},
        )

    def parse_archive_search(self, response):
        for i, item in enumerate(json.loads(response.text)["result"]["hits"]):
            il = FeedEntryItemLoader(
                response=response,
                base_url="https://{}".format(self.name),
                timezone=self._timezone,
            )
            il.add_value("path", "magazine")
            link = response.urljoin(item["detail_link"])
            il.add_value("link", link)
            try:
                author = re.sub(
                    r"(?:.*:|Von)\s*(.*)", r"\1", ", ".join(item["authors"]).title()
                )
                il.add_value("author_name", author)
            except IndexError:
                pass
            il.add_value("title", item["title"])
            # All articles have the same date.
            # We add an offset so they are sorted in the right order.
            date = response.meta["issue_date"] + timedelta(seconds=i)
            il.add_value("updated", date)
            yield scrapy.Request(link, self.parse_item_text, meta={"il": il})

    def parse_item_text(self, response):
        remove_elems = [".dachzeile", "h1", ".meta", "br", "form", ".button-container"]
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=remove_elems,
            base_url="https://{}".format(self.name),
        )
        content = response.xpath("//article").extract_first()
        if "Lesen Sie diesen Artikel in voller Länge" in content:
            il.add_value("category", "paywalled")
        il.add_value("content_html", content)
        yield il.load_item()
