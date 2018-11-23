import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class PythonPatternsGuide(FeedsSpider):
    name = "python-patterns.guide"
    start_urls = ["https://{}".format(name)]

    feed_title = "Python Patterns"
    feed_link = "https://{}".format(name)

    def parse(self, response):
        for path in response.css(".toctree-l1 > a::attr(href)").extract():
            yield scrapy.Request(response.urljoin(path), self._parse_article)

    def _parse_article(self, response):
        remove_elems = ["h1", "#contents", ".headerlink"]
        change_tags = {".admonition-title": "h2"}
        il = FeedEntryItemLoader(
            response=response,
            base_url=response.url,
            remove_elems=remove_elems,
            change_tags=change_tags,
        )
        il.add_value("link", response.url)
        il.add_value("author_name", "Brandon Rhodes")
        # Use "Last-Modified" field or fall back to "Date".
        updated = (
            response.headers.get("Last-Modified", response.headers.get("Date"))
        ).decode("ascii")
        il.add_value("updated", updated)
        il.add_css("title", "title::text")
        il.add_css("content_html", ".section")
        return il.load_item()
