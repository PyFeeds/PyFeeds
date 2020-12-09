from urllib.parse import urlparse

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class WienerZeitungAtSpider(FeedsSpider):
    name = "wienerzeitung.at"

    _titles = {}
    _ressorts = set()

    def start_requests(self):
        ressorts = self.settings.get("FEEDS_SPIDER_WIENERZEITUNG_AT_RESSORTS")
        if ressorts:
            self._ressorts = set(ressorts.split())
        else:
            self.logger.error("No ressorts given!")
            return

        for ressort in self._ressorts:
            yield scrapy.Request(
                "https://www.{}/{}".format(self.name, ressort),
                meta={"dont_cache": True, "ressort": ressort},
            )

    def feed_headers(self):
        for ressort in self._ressorts:
            yield generate_feed_header(
                title="Wiener Zeitung › {}".format(self._titles.get(ressort, ressort)),
                link="https://www.{}".format(self.name),
                icon="https://www.{}/_em_daten/wzo/favicon.ico".format(self.name),
                logo="https://www.{}/_em_daten/wzo/_layout/logo_rss.png".format(
                    self.name
                ),
                path=ressort,
            )

    def parse(self, response):
        for link in response.css(
            ".topnews-headline::attr(href), .card-title::attr(href)"
        ).extract():
            yield scrapy.Request(
                link + "?em_no_split=1",
                self._parse_article,
                meta={"ressort": response.meta["ressort"]},
            )

    def _parse_article(self, response):
        def _fix_img_src(elem):
            if "data-src-retina" in elem.attrib:
                elem.attrib["src"] = elem.attrib["data-src-retina"]
            elif "data-src" in elem.attrib:
                elem.attrib["src"] = elem.attrib["data-src"]
            return elem

        def _parse_breadcrumbs(breadcrumbs):
            links = breadcrumbs.css("a::text, a::attr('href')").extract()
            # Skip first and last "/" in URL; skip "Startseite" in breadcrumbs.
            return {urlparse(k).path[1:-1]: v for k, v in zip(links[2::2], links[3::2])}

        breadcrumbs = _parse_breadcrumbs(response.css(".breadcrumb a"))
        self._titles = {**self._titles, **breadcrumbs}

        remove_elems = [
            "noscript",
            "h1",
            ".article-meta",
            ".article-header > span.tag",
            ".article-toolbar-head",
            ".figure-copyright",
            ".new-pictures",
            ".author-item",
            ".related-articles",
            'div[data-type="advert"]',
            ".hidden",
            ".article-keywords",
            ".caption-socials",
            ".caption-text > small.d-block",
            "h2 > br",
            "h3 > br",
            ".article-socials",
        ]
        change_tags = {
            ".article-subtitle": "strong",
            "aside": "blockquote",
            "span[style='font-weight: bold;']": "strong",
            "span[style='font-style: italic;']": "em",
            ".container-inner": "blockquote",
        }
        replace_elems = {"img": _fix_img_src}
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://www.{}".format(self.name),
            remove_elems=remove_elems,
            change_tags=change_tags,
            replace_elems=replace_elems,
            timezone="Europe/Vienna",
        )
        il.add_value("link", response.url)
        il.add_css("title", 'meta[property="og:title"]::attr(content)')
        il.add_css("author_name", ".author-headline ::text")
        il.add_value("path", response.meta["ressort"])
        il.add_value("category", breadcrumbs.values())
        il.add_css("category", ".article-keywords li ::text")
        il.add_css("updated", ".article-updated time::attr('datetime')")
        il.add_css("updated", ".article-published time::attr('datetime')")
        il.add_css("content_html", "article")
        return il.load_item()
