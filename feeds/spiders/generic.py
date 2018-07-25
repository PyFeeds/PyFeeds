import io
from urllib.parse import quote_plus as urlquote_plus, urlparse, urljoin

import feedparser
import scrapy
from readability.readability import Document, Unparseable

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class GenericSpider(FeedsSpider):
    name = "generic"

    def start_requests(self):
        self._sites = self.settings.get("FEEDS_SPIDER_GENERIC_URLS")
        if not self._sites:
            self.logger.error("Please specify url(s) in the config file!")
            return

        for url in self._sites.split():
            yield scrapy.Request(url, meta={"dont_cache": True})

    def feed_headers(self):
        return []

    def parse(self, response):
        feed = feedparser.parse(io.BytesIO(response.body))
        if "entries" not in feed or not feed["entries"]:
            self.logger.error("Feed {} contains no entries!".format(response.url))
            return
        feed_entries = feed["entries"]
        feed = feed["feed"]
        path = urlquote_plus(response.url)
        yield self.generate_feed_header(
            title=feed.get("title"),
            subtitle=feed.get("subtitle"),
            link=feed["link"],
            path=path,
            author_name=feed.get("author_detail", {}).get("name"),
            logo=feed.get("image", {}).get("href"),
        )
        base_url = "://".join(urlparse(response.url)[:2])
        for entry in feed_entries:
            yield scrapy.Request(
                # Deals with protocol-relative URLs.
                urljoin(base_url, entry["link"]),
                self._parse_article,
                meta={"path": path, "feed_entry": entry, "base_url": base_url},
            )

    def _parse_article(self, response):
        doc = Document(response.text, url=response.url)
        feed_entry = response.meta["feed_entry"]
        il = FeedEntryItemLoader(base_url=response.meta["base_url"])
        il.add_value("title", doc.short_title() or feed_entry.get("title"))
        summary = feed_entry.get("summary")
        try:
            content = doc.summary(html_partial=True)
            if summary and len(summary) > len(content):
                # Something probably went wrong if the extracted content is shorter than
                # the summary.
                raise Unparseable
        except Unparseable:
            content = summary
        il.add_value("content_html", content)
        il.add_value("updated", feed_entry.get("updated", feed_entry.get("published")))
        il.add_value("author_name", feed_entry.get("author_detail", {}).get("name"))
        il.add_value("category", [t["term"] for t in feed_entry.get("tags", [])])
        il.add_value("path", response.meta["path"])
        il.add_value("link", response.url)
        yield il.load_item()
