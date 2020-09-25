from urllib.parse import urlparse

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class RisKommunalSpider(FeedsSpider):
    name = "riskommunal"
    custom_settings = {"COOKIES_ENABLED": True}
    allowed_domains = []
    cookies = {"ris-cookie": "g7750", "ris_cookie_setting": "g7750"}

    _sites = []
    _titles = {}
    _subtitles = {}
    _links = {}
    _icons = {}

    def feed_headers(self):
        for site in self._sites:
            yield generate_feed_header(
                title=self._titles.get(site),
                subtitle=self._subtitles.get(site),
                link=self._links.get(site),
                icon=self._icons.get(site),
                path=site,
            )

    def start_requests(self):
        urls = self.settings.get("FEEDS_SPIDER_RISKOMMUNAL_URLS")
        if not urls:
            self.logger.error("Please specify url(s) in the config file!")
            return

        for url in urls.split():
            parsed = urlparse(url)
            site = parsed.netloc

            self._sites.append(site)
            self._allow_domain(site)
            self._links[site] = f"{parsed.scheme}://{parsed.netloc}"

            yield scrapy.Request(
                url,
                cookies=self.cookies,
                meta={"dont_cache": True, "site": site},
            )

    def parse(self, response):
        site = response.meta["site"]

        title = response.css("meta[property='og:title']::attr('content')").get()
        self._titles[site] = title
        self._subtitles[site] = f"Neuigkeiten aus {title}"

        icon = response.css("link[rel='icon']::attr('href')").get()
        if icon and icon.startswith("/"):
            icon = f"{self._links[site]}{icon}"
        self._icons[site] = icon

        for selector in response.css("div.newslist div[class*='float_left']"):
            updated = selector.css("p.float_right::text").get()
            if not updated:
                # Do not care about "archived news"
                continue

            url = selector.css("a::attr('href')").get()
            if not url:
                # Ignore articles without a link
                continue

            if url.startswith("/"):
                url = f"{self._links[site]}{url}"

            yield scrapy.Request(
                url,
                self.parse_article,
                cookies=self.cookies,
                meta={"site": site, "updated": updated},
            )

    def parse_article(self, response):
        site = response.meta["site"]
        il = FeedEntryItemLoader(
            response=response,
            timezone="Europe/Vienna",
            base_url=self._links[site],
            dayfirst=True,
            yearfirst=False,
            remove_elems=[
                "div.main-content h1:first-of-type",
                "p#ctl00_ctl00_ctl00_cph_col_a_cph_content_cph_content_detail_p_date",
                "div#main-content-header",
            ],
        )
        il.add_value("path", site)
        il.add_value("link", response.url)
        il.add_value("updated", response.meta["updated"])
        il.add_css("title", "div.main-content h1:first-of-type::text")
        il.add_css("content_html", "div.main-content")

        yield il.load_item()

    def _allow_domain(self, domain):
        self.allowed_domains.append(domain)
        for mw in self.crawler.engine.scraper.spidermw.middlewares:
            if isinstance(mw, scrapy.spidermiddlewares.offsite.OffsiteMiddleware):
                mw.spider_opened(self)
