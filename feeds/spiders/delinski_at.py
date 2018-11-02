import json
import re
from datetime import datetime, timedelta

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class DelinskiAtSpider(FeedsSpider):
    name = "delinski.at"

    feed_title = "Delinski"
    feed_link = "https://{}".format(name)
    feed_logo = "https://{}/favicon.ico".format(name)

    def start_requests(self):
        yield scrapy.Request(
            "https://www.delinski.at/wien/restaurants",
            # The restaurants page is not cached and takes a few seconds to load.
            # Don't query more than once a day.
            meta={"cache_expires": timedelta(days=1)},
        )

    def parse(self, response):
        m = re.search("window.DELINSKI, {listViewEntities: (.*)}", response.text)
        restaurants = sorted(
            json.loads(m.group(1))["restaurants"]["entities"].values(),
            key=lambda r: int(r["created"]),
            reverse=True,
        )
        for restaurant in restaurants[:20]:
            il = FeedEntryItemLoader(timezone="UTC", base_url=response.url)
            url = response.urljoin(restaurant["url"])
            il.add_value("link", url)
            il.add_value("title", restaurant["name"])
            content = """
            <img src="{image}">
            <ul>
                <li>{address}</li>
                <li>{price_range_human}</li>
                <li>{cuisine_text}</li>
            </ul>
            """
            il.add_value("content_html", content.format(**restaurant))
            il.add_value(
                "updated", datetime.utcfromtimestamp(int(restaurant["created"]))
            )
            yield scrapy.Request(url, self._parse_restaurant, meta={"il": il})

    def _parse_restaurant(self, response):
        il = FeedEntryItemLoader(
            response=response,
            base_url=response.url,
            parent=response.meta["il"],
            remove_elems=[".external"],
        )
        il.add_css("content_html", ".content .right p")
        il.add_css("content_html", ".restaurant-link")
        il.add_css("category", ".tags a ::text")
        yield il.load_item()
