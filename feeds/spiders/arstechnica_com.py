import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class ArsTechnicaComSpider(FeedsXMLFeedSpider):
    name = "arstechnica.com"
    allowed_domains = [name]
    itertag = "item"

    _icon = (
        "https://cdn.arstechnica.net/wp-content/uploads/2016/10/"
        + "cropped-ars-logo-512_480-32x32.png"
    )
    _logo = (
        "https://cdn.arstechnica.net/wp-content/themes/ars-mobile/assets/images/"
        + "material-ars.png"
    )

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
            yield self.generate_feed_header(
                title="Ars Technica: {}".format(channel.title()),
                link="https://{}".format(self.name),
                path=channel,
            )

    def parse_node(self, response, node):
        link = node.xpath("link/text()").extract_first()
        il = FeedEntryItemLoader()
        il.add_value("title", node.xpath("title/text()").extract_first())
        il.add_value("updated", node.xpath("pubDate/text()").extract_first())
        il.add_value("category", node.xpath("category/text()").extract())
        yield scrapy.Request(
            link,
            self._parse_article,
            cookies={"view": "mobile"},
            meta={"il": il, "path": response.meta["path"], "first_page": True},
        )

    def _parse_article(self, response):
        remove_elems = [".caption-credit", ".gallery-image-credit"]
        il = FeedEntryItemLoader(
            response=response, parent=response.meta["il"], remove_elems=remove_elems
        )
        if response.meta.get("first_page", False):
            il.add_value("link", response.url)
            il.add_css("author_name", ".byline a span ::text")
            il.add_css("content_html", "header h2")
            il.add_value("path", response.meta["path"])
        il.add_css("content_html", ".article-content")
        if response.css(".next"):
            yield scrapy.Request(
                response.css(".numbers a::attr(href)").extract()[-1],
                self._parse_article,
                meta={"il": il, "path": response.meta["path"]},
            )
        else:
            yield il.load_item()
