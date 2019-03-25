import re

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider
from feeds.utils import generate_feed_header


class ArsTechnicaComSpider(FeedsXMLFeedSpider):
    name = "arstechnica.com"
    itertag = "item"

    def start_requests(self):
        channels = self.settings.get("FEEDS_SPIDER_ARSTECHNICA_COM_CHANNELS")
        if channels:
            channels = set(channels.split())
        else:
            channels = {"features"}

        for channel in channels:
            yield scrapy.Request(
                "http://feeds.{}/arstechnica/{}".format(self.name, channel),
                meta={"path": channel, "dont_cache": True},
            )

        self._channels = channels

    def feed_headers(self):
        for channel in self._channels:
            yield generate_feed_header(
                title="Ars Technica: {}".format(channel.title()),
                link="https://{}".format(self.name),
                path=channel,
                icon=(
                    "https://cdn.arstechnica.net/wp-content/uploads/2016/10/"
                    + "cropped-ars-logo-512_480-32x32.png"
                ),
                logo=(
                    "https://cdn.arstechnica.net/wp-content/themes/ars-mobile/assets/"
                    + "images/material-ars.png"
                ),
            )

    def parse_node(self, response, node):
        link = node.xpath("link/text()").extract_first()
        il = FeedEntryItemLoader()
        il.add_value("title", node.xpath("title/text()").extract_first())
        il.add_value("updated", node.xpath("pubDate/text()").extract_first())
        il.add_value("category", node.xpath("category/text()").extract())
        return scrapy.Request(
            link,
            self._parse_article,
            cookies={"view": "mobile"},
            meta={"il": il, "path": response.meta["path"], "first_page": True},
        )

    @staticmethod
    def _div_to_img(elem):
        elem.tag = "img"
        url = re.search(r"url\('([^']+)'\)", elem.attrib["style"]).group(1)
        elem.attrib["src"] = url
        elem.attrib["style"] = None
        return elem

    def _parse_article(self, response):
        remove_elems = [
            ".caption-credit",
            ".gallery-image-credit",
            "#social-left",
            "ul.toc",
            "h3:contains('Table of Contents')",
            "br",
            ".sidebar:contains('Further Reading')",
            ".credit",
        ]
        change_tags = {".sidebar": "blockquote", "aside": "blockquote"}
        replace_elems = {"div.image": self._div_to_img}
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=remove_elems,
            replace_elems=replace_elems,
            change_tags=change_tags,
        )
        if response.meta.get("first_page", False):
            il.add_value("link", response.url)
            il.add_css("author_name", ".byline a span ::text")
            il.add_css("content_html", "header h2")
            il.add_value("path", response.meta["path"])
        il.add_css("content_html", ".article-content")
        if response.css(".next"):
            return scrapy.Request(
                response.css(".numbers a::attr(href)").extract()[-1],
                self._parse_article,
                meta={"il": il, "path": response.meta["path"]},
            )
        else:
            return il.load_item()
