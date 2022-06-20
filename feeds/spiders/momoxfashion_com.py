import re
from urllib.parse import urljoin

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class MomoxFashionComSpider(FeedsSpider):
    name = "momoxfashion.com"

    _base_url = f"https://www.{name}"
    _scrape_pages = 3

    def start_requests(self):
        links = self.settings.get("FEEDS_SPIDER_MOMOXFASHION_COM_LINKS")
        if links:
            links = links.split()
        else:
            links = ["de/herren?sortiertnach=neueste"]

        for link in links:
            yield scrapy.Request(
                urljoin(self._base_url, link), meta={"dont_cache": True, "path": link}
            )

    def feed_headers(self):
        return []

    def parse(self, response):
        if len(response.css(".thumbnail")) == 0:
            self.logger.info("No items found.")
            return

        for item in response.css(".thumbnail"):
            il = FeedEntryItemLoader(selector=item, base_url=self._base_url)
            il.add_css("title", ".item_brand_text ::text")
            il.add_css("title", ".item-title ::text")
            il.add_css("title", ".current-price ::text")
            link = response.urljoin(
                re.sub(r"\?.*", "", item.css(".item-link::attr(href)").extract_first())
            )
            il.add_value("link", link)
            image_url = item.css(".item-image::attr(data-bg)").re_first(
                r"url\(([^)]+)\)"
            )
            il.add_value("content_html", f'<img src="{image_url}">')
            il.add_css("content_html", ".item-des-container")
            il.add_value("path", response.meta["path"])
            yield il.load_item()

        page = int(response.css(".pagination .active a::text").extract_first())
        if page == 1:
            yield generate_feed_header(
                title="momox fashion",
                subtitle="Deutschlands größter Second Hand-Onlineshop für "
                "Mode & Accessoires",
                icon=f"https://www.{self.name}/images/favicon-16x16.png",
                link=response.url,
                path=response.meta["path"],
            )
        if page < self._scrape_pages:
            next_page = response.css(
                ".pagination .active + li a::attr(href)"
            ).extract_first()
            if next_page:
                yield scrapy.Request(
                    response.urljoin(next_page),
                    meta={"dont_cache": True, "path": response.meta["path"]},
                )
