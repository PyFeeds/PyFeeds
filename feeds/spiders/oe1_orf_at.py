import json

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class Oe1OrfAtSpider(FeedsSpider):
    name = "oe1.orf.at"
    start_urls = ["https://audioapi.orf.at/oe1/api/json/current/broadcasts"]

    feed_title = "oe1.ORF.at"
    feed_subtitle = "Ö1 Webradio"
    feed_link = "https://oe1.orf.at"
    feed_logo = "https://{}/static/img/logo_oe1.png".format(name)

    def parse(self, response):
        for day in json.loads(response.text)[-2:]:
            for broadcast in day["broadcasts"]:
                # Only parse if already recorded (i.e. not live/in the future).
                if broadcast["state"] == "C":
                    yield scrapy.Request(broadcast["href"], self._parse_broadcast)

    def _parse_broadcast(self, response):
        broadcast = json.loads(response.text)
        il = FeedEntryItemLoader(response=response)
        link = "https://{}/player/{}/{}".format(
            self.name, broadcast["broadcastDay"], broadcast["programKey"]
        )
        il.add_value("link", link)
        il.add_value("title", broadcast["programTitle"])
        il.add_value("title", broadcast["title"])
        for stream in broadcast["streams"]:
            stream = "https://loopstream01.apa.at/?channel=oe1&id={}".format(
                stream["loopStreamId"]
            )
            il.add_value("enclosure", {"iri": stream, "type": "audio/mpeg"})
        il.add_value("updated", broadcast["niceTimeISO"])
        if broadcast["subtitle"]:
            il.add_value(
                "content_html", "<strong>{}</strong>".format(broadcast["subtitle"])
            )
        image = broadcast["images"][0]["versions"][0]
        il.add_value(
            "content_html",
            '<img src="{image[path]}" width="{image[width]}">'.format(image=image),
        )
        for item in broadcast["items"]:
            if "title" in item:
                il.add_value("content_html", "<h3>{}</h3>".format(item["title"]))
            il.add_value("content_html", item.get("description"))
        il.add_value("content_html", broadcast["description"])
        il.add_value(
            "content_html",
            '<a href="{broadcast[url]}">{broadcast[urlText]}</a>'.format(
                broadcast=broadcast
            ),
        )
        il.add_value("category", broadcast["tags"])
        if broadcast["url"] and "no_canonical_url" not in broadcast["url"]:
            return scrapy.Request(
                broadcast["url"], self._parse_show, dont_filter=True, meta={"il": il}
            )
        else:
            return il.load_item()

    def _parse_show(self, response):
        il = FeedEntryItemLoader(response=response, parent=response.meta["il"])
        il.add_css("category", ".asideBlock:first-child h2::text")
        return il.load_item()
