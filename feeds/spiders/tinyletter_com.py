import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class TinyletterComSpider(FeedsSpider):
    name = "tinyletter.com"
    allowed_domains = ["tinyletter.com"]

    _base_url = f"https://{name}"
    _titles = {}
    _subtitles = {}
    _links = {}

    def start_requests(self):
        self._accounts = self.settings.get("FEEDS_SPIDER_TINYLETTER_COM_ACCOUNTS", [])
        if self._accounts:
            self._accounts = set(self._accounts.split())
        else:
            self.logger.error("No accounts given!")
            return

        for account in self._accounts:
            yield scrapy.Request(
                f"{self._base_url}/{account}/archive?recs=1000",
                meta={"dont_cache": True, "account": account},
            )

    def feed_headers(self):
        for account in self._accounts:
            yield generate_feed_header(
                title=self._titles.get(account),
                subtitle=self._subtitles.get(account),
                link=self._links.get(account),
                icon=f"{self._base_url}/site/favicon.ico",
                logo=f"{self._base_url}/site/assets/images/brand-assets/TL_logo.svg",
                path=account,
            )

    def parse(self, response):
        account = response.meta["account"]
        self._titles[account] = response.css("title::text").get()
        self._subtitles[account] = response.css(
            "meta[property='og:description']::attr('content')"
        ).get()
        self._links[account] = f"{self._base_url}/{account}/archive"

        for u in response.css("ul.message-list a.message-link::attr('href')").getall():
            yield scrapy.Request(
                u,
                self.parse_letter,
                meta={"account": account},
            )

    def parse_letter(self, response):
        account = response.meta["account"]
        il = FeedEntryItemLoader(response=response, base_url=self._links.get(account))
        il.add_value("path", account)
        il.add_value("link", response.url)
        il.add_css("title", "title::text")
        il.add_css("author_name", "div#message-heading div.by-line a::text")
        il.add_css("updated", "div#message-heading div.date::text")
        il.add_css("content_html", "div.message-body")
        yield il.load_item()
