from datetime import datetime, timedelta

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class DerStandardAtSpider(FeedsSpider):
    name = "derstandard.at"

    _users = {}
    _titles = {}

    def start_requests(self):
        self._ressorts = self.settings.get("FEEDS_SPIDER_DERSTANDARD_AT_RESSORTS", [])
        if self._ressorts:
            self._ressorts = set(self._ressorts.split())
        else:
            self.logger.error("No ressorts given!")
            return

        for ressort in self._ressorts:
            yield scrapy.Request(
                "https://www.{}/{}".format(self.name, ressort),
                meta={"dont_cache": True, "ressort": ressort},
                # Cookie handling is disabled, so we have to send this as a header.
                headers={"Cookie": "DSGVO_ZUSAGE_V1=true"},
            )

        self._users = {
            user_id: None
            for user_id in self.settings.get(
                "FEEDS_SPIDER_DERSTANDARD_AT_USERS", ""
            ).split()
        }
        for user_id in self._users.keys():
            for page in range(3):
                yield scrapy.Request(
                    (
                        "https://apps.{}/userprofil/postings/{}?"
                        + "pageNumber={}&sortMode=1"
                    ).format(self.name, user_id, page),
                    self._parse_user_profile,
                    meta={
                        # Older pages should be cached longer.
                        "cache_expires": timedelta(hours=page),
                        "path": "userprofil/postings/{}".format(user_id),
                        "user_id": user_id,
                    },
                    headers={"Cookie": "DSGVO_ZUSAGE_V1=true"},
                )

    def feed_headers(self):
        for ressort in self._ressorts:
            yield generate_feed_header(
                title="derStandard.at › {}".format(self._titles.get(ressort, ressort)),
                subtitle="Nachrichten in Echtzeit",
                link="https://www.{}".format(self.name),
                icon="https://at.staticfiles.at/sites/mainweb/img/icons/dst/"
                "dst-16.ico",
                logo="https://at.staticfiles.at/sites/mainweb/img/icons/dst/"
                "dst-228.png",
                path=ressort,
            )

        for user_id, name in self._users.items():
            yield generate_feed_header(
                title="derStandard.at › Postings von {}".format(name),
                subtitle="Nachrichten in Echtzeit",
                link="https://apps.{}/userprofil/postings/{}".format(
                    self.name, user_id
                ),
                icon="https://at.staticfiles.at/sites/mainweb/img/icons/dst/dst-16.ico",
                logo="https://at.staticfiles.at/sites/mainweb/img/icons/dst/"
                "dst-228.png",
                path="userprofil/postings/{}".format(user_id),
            )

    def parse(self, response):
        for link in response.css("section[data-type='date'] a::attr('href')").extract():
            yield scrapy.Request(
                response.urljoin(link),
                self._parse_article,
                meta={"ressort": response.meta["ressort"]},
                headers={"Cookie": "DSGVO_ZUSAGE_V1=true"},
            )

    def _parse_article(self, response):
        def _fix_img_src(elem):
            if "src" not in elem.attrib:
                if "data-lazy-src" in elem.attrib:
                    elem.attrib["src"] = elem.attrib["data-lazy-src"]
                elif "data-src" in elem.attrib:
                    elem.attrib["src"] = elem.attrib["data-src"]
            return elem

        def _parse_breadcrumbs(breadcrumbs):
            links = breadcrumbs.css("a::text, a::attr('href')").extract()
            return {k[1:]: v for k, v in zip(links[::2], links[1::2])}

        breadcrumbs = _parse_breadcrumbs(
            response.css(".site-contextnavigation-breadcrumbs-nav a")
        )
        self._titles = {**self._titles, **breadcrumbs}

        remove_elems = [
            "ad-container",
            "figure > footer",
            "picture > button",
            "div[data-section-type='newsletter']",
            ".gallery-summary",
        ]
        change_tags = {
            ".article-subtitle": "strong",
            "aside": "blockquote",
        }
        replace_elems = {"img": _fix_img_src}
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
            change_tags=change_tags,
            replace_elems=replace_elems,
            timezone="Europe/Vienna",
        )
        il.add_value("link", response.url)
        il.add_css("title", 'meta[property="og:title"]::attr(content)')
        if response.css(".article-origins .article-author-avatar"):
            # Blog posts.
            il.add_css("author_name", ".article-author-avatar > span ::text")
        else:
            # Normal articles.
            il.add_css("author_name", ".article-origins ::text")
        il.add_value("path", response.meta["ressort"])
        il.add_value("category", breadcrumbs.values())
        il.add_css("category", ".storylabels span ::text")
        il.add_css("updated", "time::attr('datetime')")
        il.add_css("content_html", ".article-subtitle")
        il.add_css("content_html", ".article-body")
        return il.load_item()

    def _parse_user_profile(self, response):
        self._users[response.meta["user_id"]] = (
            response.css("#up_user h2::text").extract_first().strip()
        )
        for posting in response.css(".posting"):
            il = FeedEntryItemLoader(
                selector=posting,
                base_url="https://www.{}".format(self.name),
                change_tags={"span": "p"},
            )
            il.add_css("title", ".text strong::text")
            il.add_css("link", '.text a::attr("href")')
            il.add_value(
                "updated",
                datetime.utcfromtimestamp(
                    int(posting.css('.date::attr("data-timestamp")').extract_first())
                    / 1000
                ),
            )
            il.add_css("content_html", ".text span")
            il.add_css("content_html", ".article h4")
            il.add_value("path", response.meta["path"])
            yield il.load_item()
