import json
from datetime import datetime

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class IndieHackersComSpider(FeedsSpider):
    name = "indiehackers.com"

    feed_title = "Indie Hackers"
    feed_link = f"https://www.{name}"
    feed_logo = f"{feed_link}/images/favicons/favicon--192x192.png"
    feed_icon = f"{feed_link}/images/favicons/favicon--16x16.png"

    custom_settings = {"DOWNLOAD_DELAY": 1.0}

    def start_requests(self):
        yield scrapy.Request(
            "https://n86t1r3owz-1.algolianet.com/1/indexes/*/queries?"
            + "x-algolia-agent=Algolia%20for%20JavaScript%20(3.35.1)%3B%20Browser"
            + "%20(lite)&x-algolia-application-id=N86T1R3OWZ&"
            + "x-algolia-api-key=5140dac5e87f47346abbda1a34ee70c3",
            method="POST",
            body=(
                '{"requests":[{"indexName":"interviews_publishedAt_desc",'
                + '"params":"query=&page=0&hitsPerPage=20"}]}'
            ),
            meta={"dont_cache": True},
        )

    def parse(self, response):
        response = json.loads(response.text)
        interviews = response["results"][0]["hits"]
        for interview in interviews:
            yield scrapy.Request(
                f"{self.feed_link}/interview/{interview['interviewId']}",
                self._parse_interview,
                meta={
                    "categories": interview["_tags"],
                    "updated": interview["publishedAt"],
                },
            )

    def _parse_interview(self, response):
        remove_elems = [
            ".shareable-quote",
            ".share-bar",
            # Remove the last two h2s and all paragraphs below.
            ".interview-body > h2:last-of-type ~ p",
            ".interview-body > h2:last-of-type",
            ".interview-body > h2:last-of-type ~ p",
            ".interview-body > h2:last-of-type",
        ]
        il = FeedEntryItemLoader(
            timezone="UTC",
            response=response,
            base_url=self.feed_link,
            remove_elems=remove_elems,
        )
        il.add_value("link", response.url)
        il.add_css("title", "h1::text")
        il.add_css("author_name", "header .user-link__name::text")
        il.add_css("content_html", ".interview-body")
        il.add_value(
            "updated", datetime.utcfromtimestamp(response.meta["updated"] / 1000)
        )
        return il.load_item()
