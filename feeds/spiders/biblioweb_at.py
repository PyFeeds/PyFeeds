import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class BibliowebAtSpider(FeedsSpider):
    name = "biblioweb.at"
    custom_settings = {
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",
        "COOKIES_ENABLED": True,
    }

    _days = 60

    def start_requests(self):
        self._library = self.settings.get(
            "FEEDS_SPIDER_BIBLIOWEB_AT_LOCATION", ""
        ).lower()
        if self._library:
            self.feed_path = self._library
            self.feed_title = "Bibliothek {}".format(self._library.title())
            self.feed_subtitle = "Neue Titel in der {}".format(self.feed_title)
            self.feed_link = "https://www.biblioweb.at/{}/".format(self._library)
            yield scrapy.Request(
                "https://www.biblioweb.at/{}/start.asp".format(self._library),
                callback=self.parse,
                meta={"dont_cache": True},
            )
        else:
            # Key location or section biblioweb.at not found in feeds.cfg.
            self.logger.error(
                "A location is required for spider '{name}'. Please add a "
                "configuration block for '{name}' with the 'location' you "
                "want to scrape.".format(name=self.name)
            )

    def parse(self, response):
        # Ignore the initial response to start.asp as it is required to get the
        # ASP cookie. Without this cookie the requests to webopac123 (!) are
        # ignored and will be redirected to the "login" page.
        return scrapy.Request(
            "https://www.biblioweb.at/webopac123/webopac.asp"
            "?kat=1&content=show_new&seit={}&order_by=Sachtitel".format(self._days),
            callback=self.parse_overview_page,
            meta={"dont_cache": True},
        )

    def parse_overview_page(self, response):
        # Find other pages
        # Note that the dupefilter has to be enabled, otherwise already
        # parsed pages will be parsed again.
        for href in response.xpath(
            '//div[@id="p_main"][1]/div/a/div[@id!="p_aktuell"]/../@href'
        ):
            url = response.urljoin(href.extract())
            yield scrapy.Request(
                url, self.parse_overview_page, meta={"dont_cache": True}
            )

        # Find content
        for href in response.xpath('//a[contains(@href, "mnr")]/@href'):
            url = response.urljoin(href.extract())
            yield scrapy.Request(url, self.parse_content)

    def parse_content(self, response):
        parts = self._extract_parts(response)
        il = FeedEntryItemLoader(
            response=response, timezone="Europe/Vienna", dayfirst=True
        )
        il.add_value("path", self._library)
        il.add_value("title", " - ".join(parts[: self._find_first_meta(parts)]))
        il.add_value("link", response.url)
        il.add_xpath("updated", "//td/span/text()", re="In der Bibliothek seit: (.*)")

        _content = ["<ul>"]
        for part in parts:
            _content.append("<li>{}</li>".format(part))
        _content.append("</ul>")
        il.add_value("content_html", "".join(_content))
        return il.load_item()

    def _find_first_meta(self, parts):
        # Find the first entry after author | title | subtitle.
        for i, p in enumerate(parts):
            if p.count(",") == 2 or ":" in p:
                return i
        return len(parts)

    def _extract_parts(self, response):
        parts = [p.strip() for p in response.xpath("//td/span/text()").extract()]
        return [p for p in parts if p not in ("", ", ,")]
