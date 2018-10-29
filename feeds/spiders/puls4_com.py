import json
import re

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class Pusl4ComSpider(FeedsSpider):
    name = "puls4.com"
    start_urls = ["https://www.puls4.com/api/json-fe/page/sendungen"]

    feed_icon = (
        "https://www.puls4.com/bundles/wundermanpuls4/images/" + "favicon/favicon.png"
    )

    def parse(self, response):
        path = json.loads(response.text)["content"][0]["url"]
        return scrapy.Request(
            response.urljoin(path), self._parse_shows_list, meta={"dont_cache": True}
        )

    def _parse_shows_list(self, response):
        shows = json.loads(response.text)["formatOverviewItems"]
        for show in shows:
            time = re.findall(r"(\d{2}:\d{2})", show["announcement"]) or None
            if time:
                time = time[0]
            yield scrapy.Request(
                response.urljoin(show["channelUrl"] + "/videos/Ganze-Folgen"),
                self._parse_show,
                meta={
                    "dont_cache": True,
                    "time": time,
                    "handle_httpstatus_list": [404],
                },
            )

    def _parse_show(self, response):
        if response.status != 200:
            self.logger.debug("Ignoring response with status code != 200")
            return

        urls = response.css("a.media-preview-link::attr(href)").extract()[:3]
        for url in urls:
            yield scrapy.Request(
                response.urljoin(url),
                self._parse_episode,
                meta={"time": response.meta["time"]},
            )

    def _parse_episode(self, response):
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            timezone="Europe/Vienna",
            dayfirst=True,
        )
        il.add_value("link", response.url)
        il.add_xpath(
            "title",
            '//meta[@name="title"]/@content',
            re=r"(?s)(.*?)(?: vom .*)? - puls4\.com",
        )
        il.add_value(
            "updated",
            "{} {}".format(
                response.xpath('//meta[@name="title"]/@content').re_first(
                    r".*vom (\d{2}\.\d{2}\.\d{4}).*"
                ),
                response.meta["time"] or "00:00",
            ),
        )
        il.add_value(
            "content_html",
            '<img src="{}">'.format(
                response.xpath('//meta[@property="og:image"]/@content').extract_first()
            ),
        )
        il.add_css("content_html", ".player-video-description-intro::text")
        return il.load_item()
