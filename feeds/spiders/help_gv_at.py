import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class HelpGvAtSpider(FeedsSpider):
    name = "help.gv.at"
    start_urls = ["https://www.{}/Portal.Node/hlpd/public".format(name)]
    custom_settings = {
        # The redirect logic by help.gv.at relies on state saved for a session
        # so we have to limit the requests to one at a time.
        "CONCURRENT_REQUESTS": 1
    }

    feed_title = "HELP.gv.at"
    feed_subtitle = "Ihr Wegweiser durch die Behörden und Ämter in Österreich"
    feed_link = "https://www.{}".format(name)
    feed_icon = "https://www.{}/HLPD_Static/img/favicon.ico".format(name)
    feed_logo = "https://www.{}/HLPD_Static/img/120924_Header_helpgv_links.jpg".format(
        name
    )

    def parse(self, response):
        paths = ["171/Seite.1710000.html", "194/Seite.1940000.html"]
        for path in paths:
            yield scrapy.Request(
                "https://www.{}/Portal.Node/hlpd/public/content/{}".format(
                    self.name, path
                ),
                self._parse_lists,
                meta={"dont_cache": True},
            )

        yield scrapy.Request(
            (
                "https://www.{}/Portal.Node/hlpd/public/content/340/"
                + "weiterenews.html"
            ).format(self.name),
            self._parse_news,
            meta={"dont_cache": True},
        )

    def _parse_lists(self, response):
        for link in response.css(".Content > ul a::attr(href)").extract():
            yield scrapy.Request(
                response.urljoin(link), self._parse_item, meta={"dont_cache": True}
            )

    def _parse_news(self, response):
        for link in response.css(".Content article a::attr(href)").extract():
            yield scrapy.Request(response.urljoin(link), self._parse_item)

    def _parse_item(self, response):
        remove_elems = [
            "h1",
            ".nono",
            ".acceptance_org",
            ".state",
            "script",
            ".gentics-portletreload-position-notvisibleposition",
        ]
        remove_elems_xpath = [
            """
            //div[
                @class='advice' and
                child::div[@class='advice_text' and (
                    contains(., 'nicht die aktuelle Rechtslage') or
                    contains(., 'wird nicht laufend aktualisiert') or
                    contains(., 'Übersicht über bisherige "Themen des Monats"')
                )]
            ]
            """,
            # Remove table of contents.
            "//li[child::a[starts-with(@href, '#')]]",
            "//ul[not(li)]",
        ]
        change_tags = {"abbr": "span"}
        il = FeedEntryItemLoader(
            response=response,
            timezone="Europe/Vienna",
            base_url="https://www.{}".format(self.name),
            remove_elems=remove_elems,
            remove_elems_xpath=remove_elems_xpath,
            change_tags=change_tags,
            dayfirst=True,
        )
        il.add_value("link", response.url)
        il.add_xpath(
            "author_name",
            '//div[@class="acceptance_org"]/text()[preceding-sibling::br]',
        )
        il.add_css("title", "title::text", re=r"HELP.gv.at:\s*(.*)")
        il.add_value(
            "updated", response.css(".state").re_first(r"(\d{2}\.\d{2}\.\d{4})")
        )
        il.add_css("content_html", ".Content")
        return il.load_item()
