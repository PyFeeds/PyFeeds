import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class DerStandardAtSpider(FeedsXMLFeedSpider):
    name = "derstandard.at"
    allowed_domains = [name]

    _title = "derStandard.at"
    _subtitle = "Nachrichten in Echtzeit"
    _link = "https://{}".format(name)
    _icon = "https://at.staticfiles.at/sites/mainweb/img/icons/dst/dst-16.ico"
    _logo = "https://at.staticfiles.at/sites/mainweb/img/icons/dst/dst-228.png"
    _titles = {}
    # Some ressorts have articles that are regulary updated, e.g. cartoons.
    _ressorts_uncached = ["47"]
    _max_articles = 10
    _ressorts_num_articles = {}

    def start_requests(self):
        self._ressorts = self.settings.get("FEEDS_SPIDER_DERSTANDARD_AT_RESSORTS")
        if self._ressorts:
            self._ressorts = self._ressorts.split()
        else:
            self.logger.info("No ressorts given, falling back to general ressort!")
            self._ressorts = ["seite1"]

        for ressort in self._ressorts:
            if str.isnumeric(ressort):
                param = "ressortid={}".format(ressort)
            else:
                param = "ressort={}".format(ressort)
            yield scrapy.Request(
                "https://{}/?page=rss&{}".format(self.name, param),
                meta={"dont_cache": True, "ressort": ressort},
            )

    def feed_headers(self):
        for ressort in self._ressorts:
            yield self.generate_feed_header(title=self._titles[ressort], path=ressort)

    def parse_node(self, response, node):
        if response.meta["ressort"] not in self._titles:
            self._titles[response.meta["ressort"]] = node.xpath(
                "//channel/title/text()"
            ).extract_first()

        url = node.xpath("link/text()").extract_first()
        if url.startswith("https://{}/jetzt/livebericht".format(self.name)):
            return

        num_articles = self._ressorts_num_articles.get(response.meta["ressort"], 0)
        if num_articles >= self._max_articles:
            return
        self._ressorts_num_articles[response.meta["ressort"]] = num_articles + 1

        updated = node.xpath("pubDate/text()").extract_first()
        dont_cache = response.meta["ressort"] in self._ressorts_uncached
        yield scrapy.Request(
            url,
            self._parse_article,
            meta={
                "updated": updated,
                "ressort": response.meta["ressort"],
                "dont_cache": dont_cache,
            },
            cookies={"DSGVO_ZUSAGE_V1": "true"},
        )

    def _parse_article(self, response):
        remove_elems = [
            ".credits",
            ".owner-info",
            ".image-zoom",
            ".continue",
            ".sequence-number",
        ]
        change_tags = {"#media-list li": "div", "#media-list": "div"}
        replace_regex = {r'<img[^>]+data-zoom-src="([^"]+)"': r'<img src="\1"'}
        replace_elems = {
            ".embedded-posting": "<p><em>Hinweis: Das eingebettete Posting ist nur "
            + "im Artikel verfügbar.</em></p>"
        }
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
            change_tags=change_tags,
            replace_regex=replace_regex,
            replace_elems=replace_elems,
        )
        il.add_value("link", response.url)
        il.add_css("title", 'meta[property="og:title"]::attr(content)')
        il.add_css("author_name", "span.author::text")
        il.add_value("path", response.meta["ressort"])
        il.add_value("updated", response.meta["updated"])
        blog_id = response.css("#userblogentry::attr(data-objectid)").extract_first()
        if blog_id:
            url = (
                "https://{}/userprofil/bloggingdelivery/blogeintrag?godotid={}"
            ).format(self.name, blog_id)
            yield scrapy.Request(url, self._parse_blog_article, meta={"il": il})
        else:
            il.add_css("content_html", "#content-aside")
            il.add_css("content_html", "#objectContent > .copytext")
            il.add_css("content_html", "#content-main > .copytext")
            il.add_css("content_html", ".slide")
            yield il.load_item()

    def _parse_blog_article(self, response):
        il = response.meta["il"]
        il.add_value("content_html", response.text)
        yield il.load_item()
