import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class AddendumOrgSpider(FeedsXMLFeedSpider):
    name = "addendum.org"
    allowed_domains = [name]
    start_urls = ["https://www.addendum.org/feed/rss2-addendum"]

    feed_title = "Addendum"
    feed_subtitle = "das, was fehlt"
    feed_link = "https://www.{}".format(name)
    feed_icon = (
        "https://www.{}/resources/dist/favicons/android-chrome-192x192.png"
    ).format(name)
    _max_articles = 10
    _num_articles = 0

    def parse_node(self, response, node):
        url = node.xpath("link/text()").extract_first()
        if not node.xpath("category"):
            # Overview pages don't have a category.
            return
        if self._num_articles >= self._max_articles:
            # Maximum number of articles reached.
            return
        self._num_articles += 1
        yield scrapy.Request(url, self._parse_article)

    def _parse_article(self, response):
        remove_elems = [
            ".projectNav",
            "h1",
            ".socialMedia__headline",
            ".whyRead",
            ".overlayCTA",
            ".authors",
            ".socialMedia",
            ".sidebar",
            ".sectionBackground--colorTheme1",
            ".heroStage__copyright",
            ".heroStage__downLink",
            "script",
            "iframe",
            ".image__zoom ",
            ".image__copyrightWrapper",
            ".callToAction",
            ".print-action",
            ".internalLink span",
            ".addCommunity",
            ".download",
            ".BCaudioPlayer",
            "style",
            ".icon-date",
            ".callToAction__button",
            'a[href^="http://partners.webmasterplan.com/click.asp"]',
        ]
        change_tags = {
            "div.heroStage__introText": "strong",
            "figcaption": "i",
            "figure": "div",
        }
        replace_regex = {
            r'<span data-src="([^"]+)"></span>.*?<span data-src="([^"]+)" '
            + r'data-min-width="1000">': r'<a href="\2"><img src="\1"></a>',
            r'<video.*?data-placeholder="([^"]+)".*?</video>': r'<img src="\1">',
        }
        replace_elems = {
            "video": "<p><em>Hinweis: Das eingebettete Video ist nur im Artikel "
            + "verfügbar.</em></p>"
        }
        il = FeedEntryItemLoader(
            response=response,
            base_url=response.url,
            remove_elems=remove_elems,
            change_tags=change_tags,
            replace_regex=replace_regex,
            replace_elems=replace_elems,
        )
        il.add_value("link", response.url)
        il.add_css("author_name", ".sidebar .authors__name::text")
        il.add_css("title", "title::text", re="(.*) - Addendum")
        il.add_css("updated", 'meta[property="article:modified_time"]::attr(content)')
        # If not yet modified:
        il.add_css("updated", 'meta[property="article:published_time"]::attr(content)')
        il.add_css("content_html", ".content")
        yield il.load_item()
