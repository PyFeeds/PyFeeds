import io
import itertools
from urllib.parse import urljoin, urlparse

import feedparser
import readability.readability
import scrapy
from readability.readability import Document, Unparseable

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header

# Readability's output is not that interesting to justify log level "INFO".
readability.readability.log.info = readability.readability.log.debug


class GenericSpider(FeedsSpider):
    name = "generic"

    def start_requests(self):
        urls = self.settings.get("FEEDS_SPIDER_GENERIC_URLS") or ""
        fulltext_urls = self.settings.get("FEEDS_SPIDER_GENERIC_FULLTEXT_URLS") or ""
        if not urls and not fulltext_urls:
            self.logger.error("Please specify url(s) in the config file!")
            return

        for url, fulltext in itertools.chain(
            zip(urls.split(), itertools.repeat(False)),
            zip(fulltext_urls.split(), itertools.repeat(True)),
        ):
            yield scrapy.Request(
                url, meta={"dont_cache": True, "fulltext": fulltext, "path": url}
            )

    def feed_headers(self):
        return []

    def parse(self, response):
        feed = feedparser.parse(io.BytesIO(response.body))
        if "entries" not in feed or not feed["entries"]:
            self.logger.error("Feed {} contains no entries!".format(response.url))
            return
        feed_entries = feed["entries"]
        feed = feed["feed"]
        yield generate_feed_header(
            title=feed.get("title"),
            subtitle=feed.get("subtitle"),
            link=feed.get("link") or response.url,
            path=response.meta["path"],
            author_name=feed.get("author_detail", {}).get("name"),
            logo=feed.get("image", {}).get("href"),
        )
        base_url = "://".join(urlparse(response.url)[:2])
        for entry in feed_entries:
            # Deals with protocol-relative URLs.
            link = urljoin(base_url, entry["link"])
            il = FeedEntryItemLoader(base_url=base_url)
            il.add_value("path", response.meta["path"])
            il.add_value("updated", entry.get("updated") or entry.get("published"))
            il.add_value("author_name", entry.get("author_detail", {}).get("name"))
            il.add_value("link", link)
            il.add_value("category", [t["term"] for t in entry.get("tags", [])])
            if response.meta["fulltext"]:
                il.add_value("title", entry["title"])
                il.add_value("content_html", entry["content"][0]["value"])
                yield il.load_item()
            else:
                # Content is not part of the feed, scrape it.
                yield scrapy.Request(
                    link, self._parse_article, meta={"feed_entry": entry, "il": il}
                )

    def _parse_article(self, response):
        feed_entry = response.meta["feed_entry"]

        il = FeedEntryItemLoader(parent=response.meta["il"])
        try:
            response.text
        except AttributeError:
            # Response is not text (e.g. PDF, ...).
            il.add_value("title", feed_entry.get("title"))
            il.add_value("content_html", feed_entry.get("summary"))
            return il.load_item()

        doc = Document(response.text, url=response.url)
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

        return il.load_item()
