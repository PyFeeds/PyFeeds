from urllib.parse import urljoin, urlparse

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class Gem2GoSpider(FeedsSpider):
    name = "gem2go"
    custom_settings = {"COOKIES_ENABLED": True}
    allowed_domains = []
    cookies = {"ris-cookie": "g7750", "ris_cookie_setting": "g7750"}

    _sites = []
    _titles = {}
    _subtitles = {}
    _links = {}

    def feed_headers(self):
        for site in self._sites:
            yield generate_feed_header(
                title=self._titles.get(site),
                subtitle=self._subtitles.get(site),
                link=self._links.get(site),
                path=site,
            )

    def start_requests(self):
        urls = self.settings.get("FEEDS_SPIDER_GEM2GO_URLS")
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

        title = response.css("meta[property='og:title']::attr(content)").get()
        self._titles[site] = title
        self._subtitles[site] = f"Neuigkeiten aus {title}"

        # Sites use different versions of the same "CMS". Extract the "news"
        # container first and for each container scrape the article URL and the
        # publication date.
        for query_container, query_updated in [
            ("div.newslist div[class*='float_left']", "p.float_right::text"),
            (".bemCard", ".card-footer .bemContainer--date::text"),
        ]:
            for selector in response.css(query_container):
                url = selector.css("a::attr(href)").get()
                if not url:
                    # Ignore articles without a link
                    continue

                # The publication date might be present only on the overview page,
                # only on the article page or mix and match on both.
                updated = selector.css(query_updated).get()

                yield scrapy.Request(
                    urljoin(self._links[site], url),
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
                "div#main-content-header",
                "div.main-content h1:first-of-type",
                "div.newsdatum_container",
                "p#ctl00_ctl00_ctl00_cph_col_a_cph_content_cph_content_detail_p_date",
                "span.bemContainer--publishDate",
                "span.bemContainer--readingTime",
            ],
        )
        il.add_value("path", site)
        il.add_value("link", response.url)
        il.add_value("updated", response.meta["updated"])
        il.add_css("updated", ".bemContainer--publishDate ::text")
        il.add_css("updated", ".newsdatum_container ::text")
        il.add_css("updated", "p[id$='detail_p_date'] ::text")
        il.add_css("title", "div.main-content h1:first-of-type ::text")
        il.add_css("content_html", "div.main-content")

        yield il.load_item()

    def _allow_domain(self, domain):
        self.allowed_domains.append(domain)
        for mw in self.crawler.engine.scraper.spidermw.middlewares:
            if isinstance(mw, scrapy.spidermiddlewares.offsite.OffsiteMiddleware):
                mw.spider_opened(self)
