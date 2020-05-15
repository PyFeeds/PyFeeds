import json
import re
from collections import OrderedDict
from datetime import timedelta

import scrapy
from dateutil.parser import parse as dateutil_parse
from scrapy.loader.processors import MapCompose

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class FalterAtSpider(FeedsSpider):
    name = "falter.at"
    # Don't overwhelm the poor Wordpress with too many requests at once.
    custom_settings = {"DOWNLOAD_DELAY": 1.0, "COOKIES_ENABLED": True}

    def start_requests(self):
        pages = self.settings.get("FEEDS_SPIDER_FALTER_AT_PAGES")
        if pages:
            self.pages = pages.split()
        else:
            self.pages = [
                "lokalfuehrer_reviews",
                "lokalfuehrer_newest",
                "magazine",
                "streams",
            ]

        if "magazine" in self.pages:
            abonr = self.settings.get("FEEDS_SPIDER_FALTER_AT_ABONR")
            password = self.settings.get("FEEDS_SPIDER_FALTER_AT_PASSWORD")
            if abonr and password:
                yield scrapy.FormRequest(
                    url="https://www.{}/login".format(self.name),
                    formdata=OrderedDict(
                        [
                            ("login[abonr]", abonr),
                            ("login[password]", password),
                            ("redirect_url", "/archiv/"),
                        ]
                    ),
                    meta={
                        "dont_redirect": True,
                        "cache_expires": timedelta(hours=3),
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

        if "lokalfuehrer_reviews" in self.pages:
            yield scrapy.Request(
                (
                    "https://www.{}/api/lokalfuehrer/search?v=true&"
                    + "sort_pos=front&sort=review.post_date:desc&c=10"
                ).format(self.name),
                self.parse_lokalfuehrer,
                meta={"dont_cache": True, "lokalfuehrer": "reviews"},
            )

        if "lokalfuehrer_newest" in self.pages:
            yield scrapy.Request(
                (
                    "https://www.{}/api/lokalfuehrer/search?"
                    + "sort_pos=front&sort=id:desc&c=20"
                ).format(self.name),
                self.parse_lokalfuehrer,
                meta={"dont_cache": True, "lokalfuehrer": "newest"},
            )

        if "streams" in self.pages:
            yield scrapy.Request(
                ("https://www.{}/api/kino?has_stream=true&mode=movie&c=100").format(
                    self.name
                ),
                self.parse_movies,
                meta={"dont_cache": True, "movies": "streams"},
            )

        blogs = self.settings.get("FEEDS_SPIDER_FALTER_AT_BLOGS")
        if blogs:
            self.blogs = blogs.split()
        else:
            self.blogs = []

        for blog in self.blogs:
            yield scrapy.Request(
                "https://cms.falter.at/blogs/author/" + blog + "/",
                self.parse_blog_overview,
                meta={"dont_cache": True, "blog": blog},
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
            yield generate_feed_header(
                title="falter.at",
                subtitle="Wir holen dich da raus.",
                link="https://www.falter.at",
                path=path,
            )

    def parse_lokalfuehrer(self, response):
        entries = json.loads(response.text)["hits"]
        for entry in entries:
            il = FeedEntryItemLoader(
                response=response, base_url="https://{}".format(self.name)
            )
            il.add_value(
                "path", "lokalfuehrer_{}".format(response.meta["lokalfuehrer"])
            )
            il.add_value(
                "link", "https://www.{}/lokal/{}".format(self.name, entry["id"])
            )
            il.add_value("category", entry["categories"])
            il.add_value("category", entry["zip"])
            il.add_value("category", entry["city"])
            review = entry.get("review")
            if review:
                il.add_value("title", review["post_title"])
                il.add_value("title", review["post_subtitle"])
                il.add_value("author_name", review["meta"].split("|")[0].title())
                il.add_value("category", "review")
                il.add_value("updated", review["post_date"])
            else:
                il.add_value("title", entry["name"])
            for picture in entry["pictures"] or []:
                il.add_value(
                    "content_html",
                    '<img src="https://faltercdn2.falter.at/wwei/1080/{}">'.format(
                        picture["filename"]
                    ),
                )
            if review:
                il.add_value("content_html", review["post_content"])
            il.add_value("content_html", entry["category_text"])
            il.add_value(
                "content_html",
                "<p>{} {}, {}</p>".format(entry["zip"], entry["city"], entry["street"]),
            )
            if entry["location"]:
                il.add_value(
                    "content_html",
                    (
                        '<p><a href="https://www.google.com/maps?q={lat},{lon}">'
                        + "Google Maps</a></p>"
                    ).format(**entry["location"]),
                )
            yield il.load_item()

    def parse_movies(self, response):
        entries = json.loads(response.text)["hits"]
        for entry in entries:
            il = FeedEntryItemLoader(
                response=response, base_url="https://{}".format(self.name)
            )
            il.add_value("path", "{}".format(response.meta["movies"]))
            il.add_value(
                "link", "https://www.{}/kino/{}".format(self.name, entry["prod_id"])
            )
            il.add_value("title", entry["prod"])
            il.add_value("content_html", entry["comment"])
            for image in entry["images"] or []:
                il.add_value(
                    "content_html",
                    '<img src="https://faltercdn2.falter.at/events/1080/{}">'.format(
                        image["filename"]
                    ),
                )
            if "stream" in entry:
                il.add_value(
                    "content_html", '<a href="{s}">{s}</a>'.format(s=entry["stream"])
                )
            for key, value in entry.items():
                if key.startswith("has_") and value:
                    il.add_value("category", key.replace("has_", ""))
                elif key.startswith("is_") and value:
                    il.add_value("category", key.replace("is_", ""))
            il.add_value("updated", entry["index_date"])
            yield il.load_item()

    def parse_archive(self, response):
        # The perks of having a JavaScript frontend ...
        issues = json.loads(
            response.css("router-view").re_first("<router-view :data='([^']+)'>")
        )["issues"]
        latest_issue_date = dateutil_parse(
            issues[sorted(issues.keys())[-1]][-1], ignoretz=True
        )
        # The JS frontend calculates the issue number the same way, so this should be
        # somewhat official.
        issuenr = "{0[0]}{0[1]}".format(latest_issue_date.date().isocalendar())
        return scrapy.Request(
            response.urljoin("/api/archive/{}?count=1000&from=0".format(issuenr)),
            self.parse_archive_search,
            meta={"issue_date": latest_issue_date},
        )

    def parse_archive_search(self, response):
        articles = json.loads(response.text)["articles"]["hits"]
        for i, item in enumerate(articles):
            il = FeedEntryItemLoader(
                response=response,
                base_url="https://{}".format(self.name),
                timezone="Europe/Vienna",
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
            il.add_value("category", item["ressort"])
            yield scrapy.Request(link, self.parse_item_text, meta={"il": il})

    def parse_item_text(self, response):
        remove_elems = [".ad-component", ".wp-caption-text"]
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=remove_elems,
            base_url="https://{}".format(self.name),
        )
        if response.css(".bluebox"):
            il.add_value("category", "paywalled")
        il.add_css("content_html", "div.pR")
        return il.load_item()

    def parse_blog_overview(self, response):
        yield generate_feed_header(
            title=response.css("article > h1 ::text").extract_first(),
            link="https://www.falter.at",
            path="blog_{}".format(response.meta["blog"]),
        )

        for link in response.css("div[id^=post-] a::attr(href)").extract():
            yield scrapy.Request(
                link, self.parse_blog_article, meta={"blog": response.meta["blog"]}
            )

    def parse_blog_article(self, response):
        remove_elems = [".ad-component", ".wp-caption-text"]
        il = FeedEntryItemLoader(
            response=response,
            remove_elems=remove_elems,
            base_url="https://cms.{}".format(self.name),
            timezone="Europe/Vienna",
            dayfirst=True,
            yearfirst=False,
        )
        il.add_css("content_html", "article > h2")
        il.add_css("content_html", ".storycontent-article")
        il.add_css("author_name", ".falter-heading ::text", MapCompose(str.title))
        il.add_css(
            "author_name", ".thinktank-meta > span ::text", MapCompose(str.title)
        )
        il.add_css("updated", ".post > .text-label ::text", re=r"(\d{2}\.\d{2}\.\d{4})")
        il.add_value("link", response.url)
        il.add_value("path", "blog_{}".format(response.meta["blog"]))
        il.add_css("title", "article > h1 ::text")
        return il.load_item()
