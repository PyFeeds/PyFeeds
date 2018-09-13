import re

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class DieTiwagOrgSpider(FeedsXMLFeedSpider):
    name = "dietiwag.org"
    allowed_domains = [name]
    start_urls = ["http://www.dietiwag.org/rss.xml.php"]

    _title = "dietiwag.org"
    _subtitle = "die andere seite der tiroler wasser kraft"
    _link = "http://www.{}".format(name)
    _icon = "http://www.{}/favicon.ico".format(name)

    def parse_node(self, response, node):
        il = FeedEntryItemLoader(selector=node)
        url = node.xpath("link/text()").extract_first()
        il.add_value("link", url)
        il.add_xpath("updated", "pubDate/text()")
        il.add_xpath(
            "title",
            "title/text()",
            # Use re.DOTALL since some titles have newlines in them.
            re=re.compile("(?:Artikel|Tagebuch): (.*)", re.DOTALL),
        )
        yield scrapy.Request(url, self._parse_article, meta={"il": il})

    def _parse_article(self, response):
        remove_elems = [
            ".noprint",
            "form",
            ".lineall > font[size='2'] > b:first-child",
            "font[size='2'] > br:first-child",
            "font[size='2'] > br:first-child",
            "font[size='2'] > br:last-child",
            "font[size='2'] > br:last-child",
            "font[size='2'] > br:last-child",
        ]
        replace_regex = {r"\[\d{2}\.\d{2}\.\d{4}\]": "", "\xA0": ""}
        il = FeedEntryItemLoader(
            response=response,
            base_url=response.url,
            remove_elems=remove_elems,
            replace_regex=replace_regex,
            parent=response.meta["il"],
        )
        il.add_css("author_name", ".sidebar .authors__name::text")
        if response.css(".printwidth2"):
            il.add_css("content_html", ".printwidth2 > font[size='2']")
            il.add_css("content_html", ".printwidth2 > font[size='3'] > font[size='2']")
        else:
            # Tagebuch
            il.add_css("content_html", ".lineall")
            il.add_value("category", "Tagebuch")
        yield il.load_item()
