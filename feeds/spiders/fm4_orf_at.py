import json
from datetime import timedelta
from urllib.parse import urljoin

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class Fm4OrfAtSpider(FeedsSpider):
    name = "fm4.orf.at"
    allowed_domains = ["audioapi.orf.at"]
    start_urls = ["https://audioapi.orf.at/fm4/api/json/current/broadcasts"]

    _title = "fm4.ORF.at"
    _subtitle = "FM4 Player"
    _link = "https://fm4.orf.at"
    _timezone = "Europe/Vienna"
    _logo = (
        "https://tubestatic.orf.at/mojo/1_3/storyserver/tube/fm4/images/fm4.logo.svg"
    )

    def parse(self, response):
        for day in json.loads(response.text):
            for broadcast in day["broadcasts"]:
                # Only parse if already recorded (i.e. not live/in the future).
                if broadcast["state"] == "C":
                    yield scrapy.Request(broadcast["href"], self.parse_broadcast)

    @staticmethod
    def _format_date(date):
        # Yes, this is a weird datetime format.
        return date[11:19].replace(":", "") + "000"

    def parse_broadcast(self, response):
        broadcast = json.loads(response.text)
        last_item = -1
        for i, stream in enumerate(broadcast["streams"]):
            il = FeedEntryItemLoader(
                response=response, timezone=self._timezone, dayfirst=False
            )
            link = "https://{}/player/{}/{}/{}".format(
                self.name,
                broadcast["broadcastDay"],
                broadcast["programKey"][1:],
                self._format_date(stream["startISO"])
            )
            il.add_value("link", link)
            il.add_value("title", "{}: Part #{}".format(broadcast["title"], i + 1))
            il.add_value("updated", stream["startISO"])
            image = broadcast["images"][0]["versions"][-1]
            il.add_value(
                "content_html",
                '<img src="{image[path]}" width="{image[width]}">'.format(image=image)
            )
            if broadcast["subtitle"]:
                il.add_value("content_html", broadcast["subtitle"])
            if broadcast["description"]:
                il.add_value("content_html", broadcast["description"])
            iri = "https://loopstream01.apa.at/?channel=fm4&id={}".format(
                stream["loopStreamId"]
            )
            il.add_value("enclosure", {"iri": iri, "type": "audio/mpeg"})

            for item in broadcast["items"][last_item + 1:]:
                if item["start"] > stream["end"]:
                    break
                last_item += 1
                # item["title"] can be missing or None.
                if "title" not in item or not item["title"]:
                    continue
                chapter = {
                    "start": timedelta(
                        seconds=(item["start"] - stream["start"]) // 1000
                    ),
                    "href": urljoin(link, self._format_date(item["startISO"])),
                }
                if "images" in item and item["images"]:
                    chapter["image"] = item["images"][0]["versions"][-1]["path"]
                chapter["title"] = ": ".join(
                    item[s] for s in ["interpreter", "title"] if s in item
                )
                il.add_value("chapter", chapter)

            yield il.load_item()
