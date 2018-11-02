import json
from datetime import datetime, timedelta, timezone

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class AtvAtSpider(FeedsSpider):
    name = "atv.at"
    start_urls = ["https://atv.at/mediathek/neue-folgen/"]
    custom_settings = {
        # The site is really shitty, don't overwhelm it with more requests.
        "CONCURRENT_REQUESTS": 1
    }

    feed_title = "ATV.at"
    feed_subtitle = "Mediathek"
    _timerange = timedelta(days=7)

    def parse(self, response):
        for link in response.css(".program_link::attr(href)").extract():
            yield scrapy.Request(link, self.parse_item, meta={"dont_cache": True})

        for url in response.css(".topteaser_wrapper::attr(href)").extract():
            yield scrapy.Request(url, self.parse_program)

    def parse_item(self, response):
        for url in response.css(".video").xpath("../../@href").extract():
            yield scrapy.Request(url, self.parse_program)

    def parse_program(self, response):
        if not response.css(r".jsb_video\/FlashPlayer"):
            return
        data = json.loads(
            response.css(r".jsb_video\/FlashPlayer").xpath("@data-jsb").extract()[0]
        )
        data = data["config"]["initial_video"]["parts"][0]["tracking"]["nurago"]
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            timezone="Europe/Vienna",
            dayfirst=True,
        )
        il.add_value("link", data["clipurl"])
        il.add_value("title", data["programname"])
        il.add_value("updated", data["airdate"])
        il.add_xpath("content_html", '//p[@class="plot_summary"]')
        item = il.load_item()
        # Only include videos posted in the last 7 days.
        if item["updated"] + self._timerange > datetime.now(timezone.utc):
            return item
