import json
from urllib.parse import urljoin

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


def parse_article(response):
    article = json.loads(response.text)["layout"]["center"][0]
    il = FeedEntryItemLoader()
    il.add_value(
        "link", urljoin("https://{}".format(article["portal"]), article["url"])
    )
    il.add_value("title", article["title"])
    if "teaser_img" in article:
        il.add_value(
            "content_html",
            _create_figure(
                article["portal"],
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
                _create_figure(
                    article["portal"],
                    paragraph["data"]["url"].replace("large", "original"),
                    paragraph["data"].get("description"),
                ),
            )
        elif paragraph["type"] == "gallery":
            # Only include 1 image (the latest) if the feed type is article.
            # This is is a special case for comic articles where a new image is
            # added to the article once a day and it doesn't make sense to always
            # include all the old ones in the feed.
            max_images = 1 if response.meta["feed_type"] == "article" else None
            for image in paragraph["data"]["images"][:max_images]:
                il.add_value(
                    "content_html",
                    _create_figure(
                        article["portal"],
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
    il.add_value("category", article["portal"])
    if "path" in response.meta:
        il.add_value("path", response.meta["path"])
    if article["sponsored"]:
        il.add_value("category", "sponsored")
    il.add_value("category", article.get("pretitle"))
    return il.load_item()


def _create_figure(name, src, caption=None):
    src = urljoin("https://image.{}".format(name), src)
    return (
        '<figure><div><img src="{src}"></div>'
        + "<figcaption>{caption}</figcaption></figure>"
    ).format(src=src, caption=caption or "")


class KurierAtSpider(FeedsSpider):
    name = "kurier.at"

    def feed_headers(self):
        for medium in self._media:
            yield generate_feed_header(
                title="Kurier.at",
                subtitle="Minutenaktuelle Nachrichten aus Österreich und der Welt. "
                + "kurier.at - die österreichische Nachrichten-Plattform im Internet. "
                + "24 hour news from Austria's biggest quality newspaper.",
                path=medium,
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

        for channel in channels:
            yield scrapy.Request(
                "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat{}".format(
                    channel
                ),
                self._parse_channel,
                # The response should be stable since we only want to get the collection
                # for the channel so we allow caching.
                meta={"path": channel, "feed_type": "channel"},
            )

        for article in articles:
            yield scrapy.Request(
                "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat{}".format(
                    article
                ),
                parse_article,
                meta={"path": article, "dont_cache": True, "feed_type": "article"},
            )

        for author in authors:
            yield scrapy.Request(
                "https://efs.kurier.at/api/v1/cfs/route?uri=/kurierat"
                + "/author/{}".format(author),
                self._parse_author,
                # The response should be stable since we only want to get the ID for the
                # author so we allow caching.
                meta={"path": author, "feed_type": "author"},
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
                    meta={
                        "path": response.meta["path"],
                        "dont_cache": True,
                        "feed_type": response.meta["feed_type"],
                    },
                )

    def _parse_collection(self, response):
        articles = json.loads(response.text)["items"]
        for article in articles:
            if article["type"] != "empty":
                yield scrapy.Request(
                    "https://efs.kurier.at/api/v1/cfs/route?uri=/{}{}".format(
                        article["portal"].replace(".", ""), article["url"]
                    ),
                    parse_article,
                    meta={
                        "path": response.meta["path"],
                        "feed_type": response.meta["feed_type"],
                    },
                )

    def _parse_author(self, response):
        query = json.loads(response.text)["layout"]["center"][0]["query"]
        return scrapy.Request(
            "https://efs.kurier.at/api/v1/cfs/search?query={}&limit=10&page=1".format(
                query
            ),
            self._parse_search,
            meta={
                "path": response.meta["path"],
                "dont_cache": True,
                "feed_type": response.meta["feed_type"],
            },
        )

    def _parse_search(self, response):
        articles = json.loads(response.text)["articles"]
        for article in articles:
            yield scrapy.Request(
                "https://efs.kurier.at/api/v1/cfs/route?uri=/{}{}".format(
                    article["portal"].replace(".", ""), article["url"]
                ),
                parse_article,
                meta={
                    "path": response.meta["path"],
                    "feed_type": response.meta["feed_type"],
                },
            )
