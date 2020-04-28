import re
from datetime import datetime

from dateutil import rrule
from dateutil.tz import gettz
from scrapy import Request

from feeds.exceptions import DropResponse
from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class ServusTvComSpider(FeedsSpider):
    name = "servustv.com"

    feed_title = "ServusTV"
    feed_link = "https://www.servustv.com"

    def start_requests(self):
        today = datetime.now(gettz("Europe/Vienna")).replace(hour=0, minute=0, second=0)
        for day in rrule.rrule(freq=rrule.DAILY, count=14, dtstart=today):
            yield Request(
                "https://www.servustv.com/wp-admin/admin-ajax.php?"
                + "action=rbmh_tv_program_select_date&date={}".format(
                    day.strftime("%Y-%m-%d")
                ),
                # meta={"dont_cache": True},
            )

    def parse(self, response):
        for url in response.css('.component__card--link::attr("href")').extract():
            yield Request(url, self._parse_video_page)

    def _parse_video_page(self, response):
        match = re.search(
            r"https?://(?:www\.)?servustv\.com/videos/(?P<id>[aA]{2}-\w+|\d+-\d+)",
            response.url,
        )
        if not match:
            return
        video_id = match.group("id").upper()

        il = FeedEntryItemLoader(response=response)
        il.add_value("link", response.url)
        section = response.css(
            "meta[property='article:section']::attr('content')"
        ).extract_first()
        if section != "Allgemein":
            il.add_value("title", section)
        il.add_css("title", "title::text", re="(.*) - Servus TV")
        image_url = response.css(
            "meta[property='og:image']::attr('content')"
        ).extract_first()
        il.add_value("content_html", '<img src="{}">'.format(image_url))
        il.add_css("content_html", "meta[property='og:description']::attr('content')")
        il.add_css("content_html", "#media-asset-content-container")

        match = re.search(r'"dateModified":\s*"([^"]+)"', response.text)
        if match:
            il.add_value("updated", match.group(1))

        stream_url = "https://stv.rbmbtnx.net/api/v1/manifests/%s.m3u8" % video_id

        yield Request(stream_url, self._parse_stream, meta={"il": il})

    def _parse_stream(self, response):
        il = response.meta["il"]

        if response.status != 200:
            url = il.get_output_value("link")
            raise DropResponse(
                "Skipping {} because not downloadable yet".format(url), transient=True
            )

        yield il.load_item()
