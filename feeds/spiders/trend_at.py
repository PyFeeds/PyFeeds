import re
from datetime import datetime, timedelta

import scrapy
from dateutil.tz import gettz

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class TrendAtSpider(FeedsXMLFeedSpider):
    name = "trend.at"
    namespaces = [
        ("i", "http://www.google.com/schemas/sitemap-image/1.1"),
        ("rss", "http://www.sitemaps.org/schemas/sitemap/0.9"),
    ]
    itertag = "rss:url"
    iterator = "xml"

    feed_link = f"https://www.{name}"
    feed_title = "trend"
    feed_subtitle = "Das Wirtschaftsmagazin"
    feed_icon = f"{feed_link}/img/favicon-9c36f56b.ico"
    feed_logo = f"{feed_link}/img/touch/apple-touch-icon-180x180-00f104a2.png"

    def start_requests(self):
        # Scrape this and last month so that the feed is not empty on the first day of a
        # new month.
        this_month = datetime.now(gettz("Europe/Vienna")).date().replace(day=1)
        last_month = (this_month - timedelta(days=1)).replace(day=1)
        for month in [this_month, last_month]:
            yield scrapy.Request(
                "https://www.{}/sitemap-articles-{}.xml".format(
                    self.name, month.strftime("%Y-%m")
                ),
                meta={"dont_cache": True, "handle_httpstatus_list": [404]},
            )

    def parse_node(self, response, node):
        url = node.xpath("rss:loc/text()").extract_first()
        updated = node.xpath("rss:lastmod/text()").extract_first()
        return scrapy.Request(url, self.parse_item, meta={"updated": updated})

    def parse_item(self, response):
        author_date = " ".join(response.css(".author-date ::text").extract())
        match = re.search(r"von\s+(.*)", author_date)
        author_name = match.group(1) if match else "Red."

        remove_elems = [
            "aside",
            "script",
            "h1",
            "source",
            ".breadcrumbs",
            ".author-date",
            ".artikel-social-kommentar",
            ".bild-copyright",
            ".ressortTitleMobile",
            ".article-number",
            ".artikel-kommentarlink",
            ".umfrage-wrapper",
            ".articleIssueInfo",
            "hr",
            "center div[style='padding: 10px; background:#efefef']",
        ]
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
        )
        il.add_value("link", response.url)
        il.add_value("author_name", author_name)
        il.add_css("title", 'h1[itemprop="headline"]::text')
        il.add_value("updated", response.meta["updated"])
        il.add_css("content_html", "article")
        return il.load_item()
