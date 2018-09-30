import re

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class DieTiwagOrgSpider(FeedsXMLFeedSpider):
    name = "dietiwag.org"
    start_urls = ["http://www.dietiwag.org/rss.xml.php"]

    feed_title = "dietiwag.org"
    feed_subtitle = "die andere seite der tiroler wasser kraft"
    feed_link = "http://www.{}".format(name)
    feed_icon = "http://www.{}/favicon.ico".format(name)

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
        return scrapy.Request(url, self._parse_article, meta={"il": il})

    def _parse_article(self, response):
        remove_elems = [
            ".noprint",
            "form",
            "font[size='3'] > b",
            "font[size='2'] > b:first-child",
            'a[href="mailto:m.wilhelm@dietiwag.org"]',
            "br:first-child",
            "br:first-child",
            "br:first-child",
            "br:first-child",
            "br:first-child",
            "br:first-child",
            "br:last-child",
            "br:last-child",
            "br:last-child",
            "br:last-child",
            "br:last-child",
            "br:last-child",
        ]
        replace_regex = {
            r"\[\d{2}\.\d{2}\.\d{4}\]": "",
            # A0 is a non-breaking space in latin1.
            "\xA0": "",
            r"<br>\s*<br>\s*\d{1,2}\.\d{1,2}\.\d{4}\s*<br>": "",
        }
        change_attribs = {"font": {"size": None, "face": None, "color": None}}
        change_tags = {"font": "div", "center": "div"}
        il = FeedEntryItemLoader(
            response=response,
            base_url=response.url,
            remove_elems=remove_elems,
            replace_regex=replace_regex,
            change_attribs=change_attribs,
            change_tags=change_tags,
            parent=response.meta["il"],
        )
        il.add_css("author_name", ".sidebar .authors__name::text")
        if response.css(".printwidth2"):
            il.add_css("content_html", ".printwidth2")
        else:
            # Tagebuch
            il.add_css("content_html", ".lineall")
            il.add_value("category", "Tagebuch")
        return il.load_item()
