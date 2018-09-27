import re
from datetime import datetime

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class UsenixOrgSpider(FeedsSpider):
    name = "usenix.org"
    start_urls = ["https://www.usenix.org/publications/login"]

    def feed_headers(self):
        return []

    def parse(self, response):
        # Only scrape the last 8 issues.
        issues = response.css(".issues .month a::attr(href)").extract()[:8]
        yield generate_feed_header(
            title=";login:",
            subtitle="The Usenix Magazine",
            link=response.url,
            path="login",
        )
        for issue in issues:
            yield scrapy.Request(response.urljoin(issue), self.parse_login_issue)

    def parse_login_issue(self, response):
        remove_elems = [
            ".field-name-field-file-access",
            ".field-name-field-login-issue-file",
            ".field-name-field-product",
            ".field-commerce-price",
            ".views-field-field-file-access",
            ".view-header",
        ]
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://www.{}".format(self.name),
            remove_elems=remove_elems,
        )
        il.add_value("link", response.url)
        title = response.css("h1::text").extract_first().strip()
        il.add_value("title", title)
        il.add_value("updated", self._date_from_title(title))
        il.add_css("content_html", ".content-wrapper")
        il.add_value("path", "login")
        if response.css(".usenix-files-protected"):
            il.add_value("category", "paywalled")
        return il.load_item()

    def _date_from_title(self, issue):
        """Try to guess the publication date of an issue from the title."""
        match = re.search(
            r"(?P<season>Spring|Summer|Fall|Winter) (?P<year>\d{4})", issue
        )
        if match:
            seasons = {"Winter": "1", "Spring": "4", "Summer": "7", "Fall": "10"}
            month = int(seasons[match.group("season")])
            year = int(match.group("year"))
            date = datetime(day=1, month=month, year=year)
            # Issues become free after a year which should be reflected by
            # bumping the updated date by a year as well.
            date_free = datetime(day=1, month=month, year=year + 1)
            return date_free if date_free < date.utcnow() else date
        else:
            self.logger.warning('Could not extract date from title "{}"!'.format(issue))
