from datetime import datetime, timedelta

import scrapy
from dateutil.tz import gettz

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class ProfilAtSpider(FeedsSpider):
    name = "profil.at"
    allowed_domains = ["profil.at"]

    _title = "PROFIL"
    _subtitle = "Österreichs unabhängiges Nachrichtenmagazin"
    _timezone = "Europe/Vienna"
    # Parse articles from the last 3 days that have content.
    _max_days = 3
    # Don't try more than 14 days for content.
    _max_days_limit = 14

    def build_request(self, day, max_days, max_days_limit):
        return scrapy.Request(
            "https://www.{}/archiv/{}".format(self.name, day.strftime("%Y/%m/%d")),
            self.parse_archive_page,
            meta={
                "handle_httpstatus_list": [404],
                "day": day,
                "max_days": max_days,
                "max_days_limit": max_days_limit,
                "dont_cache": True,
            },
        )

    def start_requests(self):
        yield self.build_request(
            datetime.now(gettz(self._timezone)), self._max_days, self._max_days_limit
        )

    def parse_archive_page(self, response):
        day = response.meta["day"] - timedelta(days=1)
        max_days_limit = response.meta["max_days_limit"] - 1
        max_days = response.meta["max_days"]

        if response.status == 200:
            for link in response.css("h1 a::attr(href)").extract():
                yield scrapy.Request(response.urljoin(link), self.parse_item)
            max_days -= 1

        if max_days > 0 and max_days_limit > 0:
            yield self.build_request(day, max_days, max_days_limit)

    def parse_item(self, response):
        remove_elems = [
            "aside",
            "script",
            "h1",
            ".breadcrumbs",
            ".author-date",
            ".artikel-social-kommentar",
            ".bild-copyright",
            ".ressortTitleMobile",
            ".article-number",
            ".artikel-kommentarlink",
            ".umfrage-wrapper",
            ".articleIssueInfo",
        ]
        il = FeedEntryItemLoader(
            response=response,
            timezone=self._timezone,
            base_url="http://{}".format(self.name),
            remove_elems=remove_elems,
        )
        il.add_value("link", response.url)
        author_name = (
            response.css(".author-date ::text").re(r"(?:Von)?\s*(\w+ \w+)") or "Red."
        )
        il.add_value("author_name", author_name)
        il.add_css("title", 'h1[itemprop="headline"]::text')
        il.add_css("updated", 'meta[property="article:published_time"]::attr(content)')
        il.add_css("content_html", "article")
        yield il.load_item()
