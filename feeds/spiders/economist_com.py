import scrapy

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
                "https://www.{}/{}/".format(self.name, ressort),
                meta={"dont_cache": True, "ressort": ressort},
            )

    def parse(self, response):
        if not self._titles.get(response.meta["ressort"]):
            self._titles[response.meta["ressort"]] = response.css(
                "h1.section-collection-headline ::text"
            ).extract_first()

        for path in response.css(".headline-link::attr('href')").extract():
            url = response.urljoin(path)
            yield scrapy.Request(
                url, self._parse_article, meta={"ressort": response.meta["ressort"]}
            )

    def feed_headers(self):
        for ressort in self._ressorts:
            yield generate_feed_header(
                title="The Economist › {}".format(self._titles.get(ressort, ressort)),
                link="https://www.{}".format(self.name),
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
                "Skipping {} because ran into bot detection".format(response.url),
                transient=True,
            )

        remove_elems = [
            "meta",
            ".ds-share-list",
            ".advert",
            ".layout-article-links",
            ".ds-chapter-list",
            ".layout-article-meta",
        ]
        change_tags = {
            ".article__lead-image": "figure",
            ".article__description": "h2",
            ".article__footnote": "i",
        }
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
            change_tags=change_tags,
        )
        il.add_value("link", response.url)
        il.add_value("title", title)
        il.add_css("updated", "time.article__dateline-datetime::attr('datetime')")
        il.add_css("content_html", ".article__lead-image")
        il.add_css("content_html", ".article__description")
        il.add_css("content_html", ".layout-article-body")
        il.add_value("path", response.meta["ressort"])
        return il.load_item()
