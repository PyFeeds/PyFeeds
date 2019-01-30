from collections import OrderedDict

import scrapy

from feeds.exceptions import DropResponse
from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class KonsumentAtSpider(FeedsSpider):
    name = "konsument.at"
    start_urls = ["https://www.konsument.at/page/das-aktuelle-heft"]
    custom_settings = {"COOKIES_ENABLED": True}

    feed_title = "KONSUMENT.AT"
    feed_subtitle = "Objektiv, unbestechlich, keine Werbung"

    def parse(self, response):
        user = self.settings.get("FEEDS_SPIDER_KONSUMENT_AT_USERNAME")
        pwd = self.settings.get("FEEDS_SPIDER_KONSUMENT_AT_PASSWORD")
        if user and pwd:
            return scrapy.FormRequest.from_response(
                response,
                formcss="#login form",
                formdata=OrderedDict([("user", user), ("pwd", pwd)]),
                callback=self._after_login,
                meta={"dont_cache": True},
            )
        else:
            # Username, password or section not found in feeds.cfg.
            self.logger.info("Login failed: No username or password given")
            # We can still try to scrape the free articles.
            return self._after_login(response)

    def _after_login(self, response):
        if "login_failed" in response.body_as_unicode():
            self.logger.error("Login failed: Username or password wrong")
        for url in response.xpath(
            '//div[@id="content"]//a[text()!="Bestellen"]/@href'
        ).extract():
            yield scrapy.Request(
                response.urljoin(url), callback=self._parse_article_url
            )

    def _parse_article_url(self, response):
        if not response.css("#content"):
            raise DropResponse(
                "Skipping {} since it is empty".format(response.url), transient=True
            )

        if "Fehler" in response.css("h2 ::text").extract_first():
            raise DropResponse(
                "Skipping {} since it returned an error".format(response.url),
                transient=True,
            )

        remove_elems = ['div[style="padding-top:10px;"]']
        il = FeedEntryItemLoader(
            response=response,
            timezone="Europe/Vienna",
            base_url="https://{}".format(self.name),
            dayfirst=True,
            remove_elems=remove_elems,
        )
        il.add_value("link", response.url)
        il.add_value("author_name", "VKI")
        date = response.css(".issue").re_first(
            r"veröffentlicht:\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})"
        )
        il.add_value("updated", date)
        url = response.xpath('//a[text()="Druckversion"]/@onclick').re_first(
            r"window\.open\('(.*)'\);"
        )
        il.add_css("title", "h1::text")
        if url:
            return scrapy.Request(
                response.urljoin(url), callback=self._parse_article, meta={"il": il}
            )
        else:
            il.add_value("category", "paywalled")
            il.add_css("content_html", ".primary")
            il.add_css("content_html", 'div[style="padding-top:10px;"] > h3')
            return il.load_item()

    def _parse_article(self, response):
        remove_elems = ["#issue", "h1", "#slogan", "#logo", "#footer"]
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
        )
        il.add_css("content_html", "#page")
        return il.load_item()
