import scrapy
import datetime

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class ZeitdiebinAtSpider(FeedsSpider):
    name = "zeit.diebin.at"
    allowed_domains = ["zeit.diebin.at"]
    start_urls = ["https://zeit.diebin.at/upcoming"]

    _title = "zeitdiebin"
    _subtitle = "irgendwas ist immer ..."
    _link = "https://{}".format(name)
    _logo = "https://{}/favicon.ico".format(name)
    _timezone = "Europe/Vienna"

    def parse(self, response):
        for link in response.css("a[href*=events]::attr(href)").re(r"events/\d+"):
            yield scrapy.Request(response.urljoin(link), self.parse_item)

    def parse_item(self, response):
        il = FeedEntryItemLoader(
            response=response,
            base_url="{}/".format(self._link),
            timezone=self._timezone,
            dayfirst=True,
            remove_elems=[".ruler", "h1"],
        )

        il.add_css("title", "h1.event-title::text")
        il.add_value("link", response.url)

        date = response.css("title").re_first(r"(\d{2}\.\d{2}\.\d{4})")
        time = response.css("title").re_first(r"(\d{2}:\d{2})") or ""
        if date:
            il.add_value("updated", "{} {}".format(date, time))
        else:
            day_month = response.css("title").re_first(r"\d{2}\.\d{2}")
            if day_month:
                il.add_value(
                    "updated",
                    "{}.{} {}".format(day_month, datetime.datetime.now().year, time),
                )
            else:
                pass
                # Item is skipped.

        il.add_css("content_html", "div#content.container")

        yield il.load_item()


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
