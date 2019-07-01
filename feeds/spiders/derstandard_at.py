from datetime import datetime, timedelta

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider
from feeds.utils import generate_feed_header


class DerStandardAtSpider(FeedsXMLFeedSpider):
    name = "derstandard.at"
    custom_settings = {"COOKIES_ENABLED": False}

    _titles = {}

    def start_requests(self):
        self._ressorts = self.settings.get("FEEDS_SPIDER_DERSTANDARD_AT_RESSORTS")
        if self._ressorts:
            self._ressorts = set(self._ressorts.split())
        else:
            self._ressorts = set([""])
            self.logger.info("No ressorts given, falling back to general feed!")

        for ressort in self._ressorts:
            ressort = ressort.split("/")[0]
            yield scrapy.Request(
                "https://www.{}/rss/{}".format(self.name, ressort),
                meta={"dont_cache": True, "ressort": ressort},
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
            # Only generate feed header if page already scraped and title known.
            if ressort in self._titles:
                yield generate_feed_header(
                    title="derStandard.at › {}".format(self._titles[ressort]),
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

    def parse_node(self, response, node):
        url = node.xpath("link/text()").extract_first()
        if url.startswith("https://www.{}/jetzt/livebericht".format(self.name)):
            return

        updated = node.xpath("pubDate/text()").extract_first()
        return scrapy.Request(
            url,
            self._parse_article,
            meta={"updated": updated, "ressort": response.meta["ressort"]},
            # Cookie handling is disabled, so we have to send this as a header.
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
        paths = self._ressorts.intersection(breadcrumbs.keys())
        if not paths:
            return

        remove_elems = [
            "ad-container",
            "figure > footer",
            "picture > button",
            "div[data-section-type='newsletter']",
            ".gallery-summary",
        ]
        change_tags = {".article-subtitle": "strong", "aside": "blockquote"}
        replace_elems = {"img": _fix_img_src}
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
            change_tags=change_tags,
            replace_elems=replace_elems,
        )
        il.add_value("link", response.url)
        il.add_css("title", 'meta[property="og:title"]::attr(content)')
        il.add_css("author_name", ".article-origins ::text")
        self._titles = {**self._titles, **breadcrumbs}
        il.add_value("path", paths)
        il.add_value("category", breadcrumbs.values())
        il.add_value("updated", response.meta["updated"])
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
