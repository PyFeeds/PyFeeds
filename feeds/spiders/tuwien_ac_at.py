import json
import re

import scrapy
from inline_requests import inline_requests

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class TuWienAcAtSpider(FeedsSpider):
    name = "tuwien.ac.at"

    feed_title = "TU Wien: Mitteilungsblätter"
    feed_icon = "https://{}/favicon.ico".format(name)

    def start_requests(self):
        yield scrapy.Request(
            "https://tiss.{}/mbl/main/uebersicht".format(self.name),
            headers={"Accept-Language": "de-DE,de"},
            meta={"dont_cache": True},
        )

    @inline_requests
    def parse(self, response):
        mitteilungsblaetter = response.css(".mitteilungsblaetter")
        updated = mitteilungsblaetter.css("::text").re_first(r"(\d{2}\.\d{2}\.\d{4})")
        link = response.urljoin(
            mitteilungsblaetter.css('a::attr("href")').extract_first()
        )

        response = yield scrapy.Request(link, method="HEAD")
        mb_url = response.url
        match = re.search(
            r"https://tiss.tuwien.ac.at/mbl/blatt_struktur/anzeigen/(\d+)", mb_url
        )
        if not match:
            self.logger.error("No Mitteilungsblätter found!")
            return
        else:
            mb_id = match.group(1)

        url = "https://tiss.{}/api/mbl/v22/id/{}".format(self.name, mb_id)
        response = yield scrapy.Request(url)

        last_entry = None
        for entry in reversed(json.loads(response.text)["knoten"]):
            (entry["main"], entry["sub"]) = re.match(
                r"(\d+)\.?(\d*)", entry["counter"]
            ).groups()
            if last_entry is not None and last_entry["main"] == entry["main"]:
                entry["inhalt"] += "<h2>{}</h2>".format(last_entry["titel"])
                entry["inhalt"] += last_entry["inhalt"]
            if entry["sub"] == "":
                il = FeedEntryItemLoader(
                    base_url="https://tiss.{}".format(self.name),
                    timezone="Europe/Vienna",
                    dayfirst=True,
                )
                il.add_value("updated", updated)
                il.add_value("link", mb_url + "#{}".format(entry["counter"]))
                il.add_value("title", entry["titel"])
                il.add_value("content_html", entry["inhalt"])
                yield il.load_item()
                last_entry = None
            else:
                last_entry = entry
