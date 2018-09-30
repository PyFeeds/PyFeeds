import json
import scrapy
from urllib.parse import urljoin, quote_plus as urlquote_plus

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class KurierAtSpider(FeedsSpider):
    name = "kurier.at"

    def feed_headers(self):
        for medium in self._media:
            yield generate_feed_header(
                title="Kurier.at",
                subtitle="Minutenaktuelle Nachrichten aus Österreich und der Welt. "
                + "kurier.at - die österreichische Nachrichten-Plattform im Internet. "
                + "24 hour news from Austria's biggest quality newspaper.",
                path=urlquote_plus(medium),
                link="https://www.{}".format(self.name),
                logo="https://{}/assets/logos/logo.png".format(self.name),
            )

    def start_requests(self):
        channels = self.settings.get("FEEDS_SPIDER_KURIER_AT_CHANNELS", "").split()
        articles = self.settings.get("FEEDS_SPIDER_KURIER_AT_ARTICLES", "").split()
        authors = self.settings.get("FEEDS_SPIDER_KURIER_AT_AUTHORS", "").split()
        if not any([channels, articles, authors]):
            self.logger.error(
                "Please specify what to crawl for kurier.at in config file!"
            )
            self._media = []
            return

        self._media = channels + articles + authors

        if channels:
            for channel in channels:
                yield scrapy.Request(
                    "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat{}".format(
                        channel
                    ),
                    self._parse_channel,
                    # The response should be stable since we only want to get the
                    # collection for the channel so we allow caching.
                    meta={"path": urlquote_plus(channel)},
                )

        if articles:
            for article in articles:
                yield scrapy.Request(
                    "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat{}".format(
                        article
                    ),
                    self._parse_article,
                    meta={"path": urlquote_plus(article), "dont_cache": True},
                )

        if authors:
            for author in authors:
                yield scrapy.Request(
                    "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat"
                    + "/author/{}".format(author),
                    self._parse_author,
                    # The response should be stable since we only want to get the ID for
                    # the author so we allow caching.
                    meta={"path": urlquote_plus(author)},
                )

    def _parse_channel(self, response):
        for block in json.loads(response.text)["layout"]["center"]:
            if block["type"] == "longList":
                return scrapy.Request(
                    (
                        "https://efs.kurier.at/api/v1/cfs/collection/{}"
                        + "?start=0&limit=20"
                    ).format(block["collectionName"]),
                    self._parse_collection,
                    meta={"path": response.meta["path"], "dont_cache": True},
                )

    def _parse_collection(self, response):
        articles = json.loads(response.text)["items"]
        for article in articles:
            yield scrapy.Request(
                "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat{}".format(
                    article["url"]
                ),
                self._parse_article,
                meta={"path": response.meta["path"]},
            )

    def _create_figure(self, src, caption=None):
        src = urljoin("https://image.{}".format(self.name), src)
        return (
            '<figure><div><img src="{src}"></div>'
            + "<figcaption>{caption}</figcaption></figure>"
        ).format(src=src, caption=caption or "")

    def _parse_article(self, response):
        article = json.loads(response.text)["layout"]["center"][0]
        il = FeedEntryItemLoader()
        il.add_value("link", urljoin("https://{}".format(self.name), article["url"]))
        il.add_value("title", article["title"])
        if "teaser_img" in article:
            il.add_value(
                "content_html",
                self._create_figure(
                    article["teaser_img"]["url"],
                    article["teaser_img"].get("description"),
                ),
            )
        il.add_value(
            "content_html", "<p><strong>{}</strong></p>".format(article["teaser_text"])
        )
        for paragraph in article["paragraphs"]:
            if paragraph["type"] == "text":
                il.add_value("content_html", paragraph["data"]["html"])
            elif paragraph["type"] == "youtube":
                url = "https://www.youtube.com/watch?v={}".format(
                    paragraph["data"]["videoid"]
                )
                il.add_value(
                    "content_html",
                    '<div><a href="{url}">{url}</a></div>'.format(url=url),
                )
            elif paragraph["type"] == "image":
                il.add_value(
                    "content_html",
                    self._create_figure(
                        paragraph["data"]["url"].replace("large", "original"),
                        paragraph["data"].get("description"),
                    ),
                )
            elif paragraph["type"] == "gallery":
                for image in paragraph["data"]["images"][:1]:
                    il.add_value(
                        "content_html",
                        self._create_figure(
                            image["url"].replace("large", "original"),
                            image.get("description"),
                        ),
                    )
        il.add_value("updated", article["updated_date"])
        for author in article["authors"]:
            il.add_value("author_name", "{firstname} {lastname}".format(**author))
        if not article["authors"]:
            il.add_value("author_name", article["agency"])
        il.add_value("category", article["channel"]["name"])
        il.add_value("path", response.meta["path"])
        if article["sponsored"]:
            il.add_value("category", "sponsored")
        il.add_value("category", article.get("pretitle"))
        return il.load_item()

    def _parse_author(self, response):
        query = json.loads(response.text)["layout"]["center"][0]["query"]
        return scrapy.Request(
            "https://efs.kurier.at/api/v1/cfs/search?query={}&limit=10&page=1".format(
                query
            ),
            self._parse_search,
            meta={"path": response.meta["path"], "dont_cache": True},
        )

    def _parse_search(self, response):
        articles = json.loads(response.text)["articles"]
        for article in articles:
            yield scrapy.Request(
                "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat{}".format(
                    article["url"]
                ),
                self._parse_article,
                meta={"path": response.meta["path"]},
            )
