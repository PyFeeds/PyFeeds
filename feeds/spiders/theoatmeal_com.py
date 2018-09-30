from urllib.parse import urlsplit

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class TheOatmealComSpider(FeedsXMLFeedSpider):
    name = "theoatmeal.com"
    start_urls = ["http://theoatmeal.com/feed/rss"]

    namespaces = [
        ("dc", "http://purl.org/dc/elements/1.1/"),
        ("def", "http://purl.org/rss/1.0/"),
    ]
    iterator = "xml"
    itertag = "def:item"

    feed_title = "The Oatmeal"
    feed_subtitle = (
        "The oatmeal tastes better than stale skittles found under the couch cushions"
    )
    _base_url = "https://{}".format(name)
    feed_icon = "https://{}/favicon.ico".format(name)
    feed_logo = (
        "http://s3.amazonaws.com/theoatmeal-img/default/header2016/logo_rainbow.png"
    )

    def parse_node(self, response, node):
        url = node.xpath("def:link/text()").extract_first()
        author_name = node.xpath("dc:creator/text()").extract_first()
        updated = node.xpath("dc:date/text()").extract_first()
        return scrapy.Request(
            url, self.parse_item, meta={"updated": updated, "author_name": author_name}
        )

    def parse_item(self, response):
        il = FeedEntryItemLoader(response=response, base_url=self._base_url)
        il.add_value("updated", response.meta["updated"])
        il.add_value("author_name", response.meta["author_name"])
        il.add_value("link", response.url)
        il.add_css("title", "title::text", re="(.*) - The Oatmeal")
        il.add_value("category", urlsplit(response.url).path.strip("/").split("/")[0])

        # comics
        il.add_css("content_html", "#comic > img")
        il.add_css("content_html", "#comic > p > img")

        # blog
        il.add_css("content_html", "#blog .center_text img")
        return il.load_item()
