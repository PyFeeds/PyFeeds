import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider
from feeds.utils import generate_feed_header


class FtComSpider(FeedsXMLFeedSpider):
    name = "ft.com"
    custom_settings = {"REFERER_ENABLED": False}

    _titles = {}

    def start_requests(self):
        self._ressorts = self.settings.get("FEEDS_SPIDER_FT_COM_RESSORTS", [])
        if self._ressorts:
            self._ressorts = set(self._ressorts.split())
        else:
            self._ressorts = set(["homepage"])

        for ressort in self._ressorts:
            if ressort == "homepage":
                path = ""
            else:
                path = ressort
            yield scrapy.Request(
                "https://www.{}/{}?format=rss".format(self.name, path),
                meta={"dont_cache": True, "ressort": ressort},
            )

    def parse_node(self, response, node):
        if not self._titles.get(response.meta["ressort"]):
            self._titles[response.meta["ressort"]] = response.xpath(
                "//channel/title/text()"
            ).extract_first()

        url = node.xpath("link/text()").extract_first()
        return scrapy.Request(
            url,
            self._parse_article,
            meta={"ressort": response.meta["ressort"]},
            headers={"Referer": "https://www.facebook.com"},
        )

    def feed_headers(self):
        for ressort in self._ressorts:
            yield generate_feed_header(
                title="Financial Times › {}".format(self._titles.get(ressort, ressort)),
                link="https://www.{}".format(self.name),
                icon=(
                    "https://www.{}/__origami/service/image/v2/images/raw/"
                    + "ftlogo-v1%3Abrand-ft-logo-square-coloured?source=update-logos"
                    + "&width=32&height=32&format=png"
                ).format(self.name),
                logo=(
                    "https://www.{}/__origami/service/image/v2/images/raw/"
                    + "ftlogo-v1%3Abrand-ft-logo-square-coloured?source=update-logos"
                    + "&width=194&height=194&format=png"
                ).format(self.name),
                path=ressort,
            )

    def _parse_article(self, response):
        remove_elems = [".n-content-recommended--single-story"]
        change_tags = {".topper__standfirst": "h2"}
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
            change_tags=change_tags,
        )
        il.add_value("link", response.url)
        il.add_css("title", 'meta[property="og:title"]::attr(content)')
        il.add_css("author_name", 'meta[property="article:author"]::attr(content)')
        il.add_css("updated", 'meta[property="article:modified_time"]::attr(content)')
        il.add_css("content_html", ".topper__standfirst")
        il.add_css("content_html", ".article__content-body")
        il.add_css("category", ".n-content-ta ::text")
        il.add_value("path", response.meta["ressort"])
        return il.load_item()
