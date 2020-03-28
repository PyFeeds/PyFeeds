from urllib.parse import urljoin

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class FlimmitComSpider(FeedsSpider):
    name = "flimmit.com"

    _base_url = "https://www.{}".format(name)
    _categories = ["filme", "serien", "europa", "kinder"]

    def start_requests(self):
        categories = self.settings.get("FEEDS_SPIDER_FLIMMIT_COM_CATEGORIES")
        if categories:
            self._categories = categories.split()

        for category in self._categories:
            yield scrapy.Request(
                urljoin(
                    self._base_url,
                    "https://www.flimmit.com/{}/?dir=desc&order=news_from_date".format(
                        category
                    ),
                ),
                meta={"dont_cache": True, "path": category},
            )

    def feed_headers(self):
        for category in self._categories:
            yield generate_feed_header(
                title="Flimmit.com: {}".format(category.title()),
                link="https://www.{}".format(self.name),
                icon="https://www.{}/favicon.ico".format(self.name),
                path=category,
            )

    @staticmethod
    def _fix_img_src(elem):
        if "data-original" in elem.attrib:
            elem.attrib["src"] = elem.attrib["data-original"]
        return elem

    def parse(self, response):
        for link in response.css(
            ".category-products .item .product-image::attr('href')"
        ).extract():
            yield scrapy.Request(
                link, self._parse_item, meta={"path": response.meta["path"]}
            )

    @staticmethod
    def _create_attributes_html(keys, values):
        attr_html = "<ul>"
        for key, value in zip(keys, values):
            attr_html += "<li><strong>{key}</strong> {value}</li>".format(
                key=key, value=value
            )
        attr_html += "</ul>"
        return attr_html

    def _parse_item(self, response):
        if response.css(".product-package"):
            yield from self.parse(response)
        else:
            remove_elems = [
                "h1",
                "h6",
                "img[src*='overlay-europa']",
                ".product-attr-useraction",
                ".product-award",
                ".product-image",
                ".bundle-seasons",
            ]
            replace_elems = {"img": self._fix_img_src}
            change_tags = {"div.attr-text": "strong"}

            il = FeedEntryItemLoader(
                response=response,
                base_url=self._base_url,
                remove_elems=remove_elems,
                replace_elems=replace_elems,
                change_tags=change_tags,
            )

            il.add_css("title", "h1 ::text")
            il.add_value("link", response.url)
            il.add_value("path", response.meta["path"])

            il.add_css("content_html", ".product-description .product-image img")
            attributes = self._create_attributes_html(
                [
                    e.strip()
                    for e in response.css(
                        ".product-attributes .col-xs-5 ::text"
                    ).extract()
                    if e.strip()
                ],
                [
                    e.strip()
                    for e in response.css(
                        ".product-attributes .col-xs-7 ::text"
                    ).extract()
                    if e.strip()
                ],
            )
            il.add_value("content_html", attributes)
            il.add_css("content_html", ".product-info .item")

            if (
                "abo"
                in response.css(
                    ".product-description img::attr('data-overlay')"
                ).extract_first()
            ):
                il.add_value("category", "abo")
            il.add_css("category", "span[itemprop='genre']::text")
            # Kollektionen
            il.add_css(
                "category",
                ".product-info .item > div.attr-text:last-of-type ~ a ::text",
            )

            yield il.load_item()
