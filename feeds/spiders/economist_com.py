import scrapy
from itemloaders.processors import TakeFirst

from feeds.exceptions import DropResponse
from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class EconomistComSpider(FeedsSpider):
    name = "economist.com"
    # Don't send too many requests to not trigger the bot detection.
    custom_settings = {"DOWNLOAD_DELAY": 5.0}

    _titles = {}

    def start_requests(self):
        # See https://www.economist.com/rss for a list of ressorts.
        self._ressorts = self.settings.get("FEEDS_SPIDER_ECONOMIST_COM_RESSORTS", [])
        if self._ressorts:
            self._ressorts = set(self._ressorts.split())
        else:
            self.logger.error("No ressorts given!")
            return

        for ressort in self._ressorts:
            yield scrapy.Request(
                f"https://www.{self.name}/{ressort}",
                meta={"dont_cache": True, "ressort": ressort},
            )

    def parse(self, response):
        if not self._titles.get(response.meta["ressort"]):
            self._titles[response.meta["ressort"]] = response.css(
                "h1.section-collection-headline ::text"
            ).extract_first()

        for path in response.css("h3 a::attr('href')").extract():
            url = response.urljoin(path)
            yield scrapy.Request(
                url, self._parse_article, meta={"ressort": response.meta["ressort"]}
            )

    def feed_headers(self):
        for ressort in self._ressorts:
            yield generate_feed_header(
                title=f"The Economist › {self._titles.get(ressort, ressort)}",
                link=f"https://www.{self.name}",
                icon="https://www.{}/engassets/ico/favicon.f1ea9088.ico".format(
                    self.name
                ),
                logo=(
                    "https://www.{}/engassets/ico/touch-icon-180x180.f1ea9088.png"
                ).format(self.name),
                path=ressort,
            )

    def _parse_article(self, response):
        title = response.css('meta[property="og:title"]::attr(content)').extract_first()
        if not title:
            raise DropResponse(
                f"Skipping {response.url} because ran into bot detection",
                transient=True,
            )

        change_tags = {
            "small": "span",
            ".article-text": "p",
        }
        il = FeedEntryItemLoader(
            response=response, base_url=f"https://{self.name}", change_tags=change_tags
        )
        il.add_value("link", response.url)
        il.add_value("title", title)
        il.add_css("updated", "time::attr('datetime')")
        il.add_css("content_html", "article section figure img", TakeFirst())
        il.add_css("content_html", "article section h2")
        il.add_css(
            "content_html",
            ".article__body-text, .article-text, article__body-text-image",
        )
        il.add_value("path", response.meta["ressort"])
        return il.load_item()
