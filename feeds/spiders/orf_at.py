import json
import re
from urllib.parse import urlparse

import lxml
import scrapy
from inline_requests import inline_requests
from scrapy.selector import Selector

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider
from feeds.utils import generate_feed_header


class OrfAtSpider(FeedsXMLFeedSpider):
    name = "orf.at"
    namespaces = [
        ("dc", "http://purl.org/dc/elements/1.1/"),
        ("orfon", "http://rss.orf.at/1.0/"),
        ("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
        # Default (empty) namespaces are not supported so we just come up with one.
        ("rss", "http://purl.org/rss/1.0/"),
    ]
    itertag = "rss:item"
    # Use XML iterator instead of regex magic which would fail due to the
    # introduced rss namespace prefix.
    iterator = "xml"

    def start_requests(self):
        channels = self.settings.get("FEEDS_SPIDER_ORF_AT_CHANNELS")
        if channels:
            channels = set(channels.split())
        else:
            channels = {"news"}
        available_channels = {
            "burgenland",
            "fm4",
            "help",
            "kaernten",
            "news",
            "noe",
            "oe3",
            "oesterreich",
            "ooe",
            "religion",
            "salzburg",
            "science",
            "sport",
            "steiermark",
            "tirol",
            "vorarlberg",
            "wien",
        }
        unknown_channels = channels - available_channels
        if unknown_channels:
            self.logger.warning(
                "Unknown channel(s) in config file: {}".format(
                    ", ".join(unknown_channels)
                )
            )

        for channel in channels:
            yield scrapy.Request(
                "https://rss.orf.at/{}.xml".format(channel),
                meta={"path": channel, "dont_cache": True},
            )

        self._channels = channels

        self._authors = [
            author
            for author in (
                self.settings.get("FEEDS_SPIDER_ORF_AT_AUTHORS", "").split("\n")
            )
            if author
        ]

    def feed_headers(self):
        for channel in self._channels:
            channel_url = "{}.ORF.at".format(channel)
            yield generate_feed_header(
                title=channel_url,
                link="https://{}".format(channel_url.lower()),
                path=channel,
                logo=self._get_logo(channel),
            )

        for author in self._authors:
            yield generate_feed_header(title="ORF.at: {}".format(author), path=author)

    def parse(self, response):
        selector = Selector(response, type="xml")

        doc = lxml.etree.ElementTree(lxml.etree.fromstring(response.body))
        if doc.getroot().nsmap:
            self._register_namespaces(selector)
            nodes = selector.xpath("//%s" % self.itertag)
        else:
            nodes = selector.xpath("//item")

        return self.parse_nodes(response, nodes)

    def parse_node(self, response, node):
        if "orfon" in node.namespaces:
            return self._parse_extended_node(response, node)
        else:
            return self._parse_simple_node(response, node)

    def _parse_extended_node(self, response, node):
        categories = [
            node.xpath("orfon:storyType/@rdf:resource").re_first("urn:orfon:type:(.*)"),
            node.xpath("dc:subject/text()").extract_first(),
        ]
        substories = node.xpath(
            "orfon:substories/rdf:Bag/rdf:li/@rdf:resource"
        ).extract()
        updated = node.xpath("dc:date/text()").extract_first()
        meta = {
            "path": response.meta["path"],
            "categories": categories,
            "updated": updated,
        }
        if substories:
            links = substories
        else:
            links = [node.xpath("rss:link/text()").extract_first()]
        for link in links:
            fixed_link = self._extract_link(link)
            if fixed_link is None or any(
                fixed_link.startswith(url)
                for url in ["https://debatte.orf.at", "https://iptv.orf.at"]
            ):
                self.logger.debug(
                    "Ignoring link to '{}' ('{}')".format(link, fixed_link)
                )
            else:
                yield scrapy.Request(fixed_link, self._parse_article, meta=meta)

    def _parse_simple_node(self, response, node):
        meta = {
            "path": response.meta["path"],
            "categories": node.xpath("category/text()").extract(),
            "updated": node.xpath("pubDate/text()").extract_first(),
        }
        link = node.xpath("link/text()").extract_first()
        return scrapy.Request(link, self._parse_article, meta=meta)

    @staticmethod
    def _extract_link(link):
        """Extract a working link from a possibly broken link."""
        if link is None:
            return None
        match = re.search(r"https?://(?:[^\.]+\.)?orf\.at/(?:news/)?stories/\d*", link)
        return match.group(0) + "/" if match else None

    @inline_requests
    def _parse_article(self, response):
        # Heuristic for news.ORF.at to to detect teaser articles.
        more = self._extract_link(
            response.css(
                ".story-story p > strong:contains('Mehr') + a::attr(href), "
                + ".story-story p > a:contains('Lesen Sie mehr')::attr(href)"
            ).extract_first()
        )
        if more and more != response.url:
            self.logger.debug("Detected teaser article, redirecting to {}".format(more))
            response = yield scrapy.Request(more, meta=response.meta)

        remove_elems = [
            ".byline",
            "h1",
            ".socialshare",
            ".socialShareWrapper",
            ".socialButtons",
            ".credit",
            ".toplink",
            ".offscreen",
            ".storyMeta",
            "script",
            ".oon-youtube-logo",
            ".vote",
            # redesign
            "#more-to-read-anchor",
            ".social-buttons",
            ".story-horizontal-ad",
            ".linkcard",
            ".geolocation",  # Bundesländer
        ]
        pullup_elems = {
            ".remote .slideshow": 1,
            ".remote .instagram": 1,
            ".remote .facebook": 1,
            ".remote .twitter": 1,
            ".remote .youtube": 1,
            ".remote table": 1,
        }
        replace_elems = {
            ".video": "<p><em>Hinweis: Das eingebettete Video ist nur im Artikel "
            + "verfügbar.</em></p>",
            ".slideshow": (
                "<p><em>Alte Slideshows werden nicht mehr unterstützt.</em></p>"
            ),
        }
        change_attribs = {"img": {"data-src": "src", "srcset": "src"}}
        change_tags = {
            ".image": "figure",
            ".caption": "figcaption",
            ".fact": "blockquote",  # FM4
        }
        author, author_selector = self._extract_author(response)
        if author:
            self.logger.debug("Extracted possible author '{}'".format(author))
            # Remove the paragraph that contains the author.
            remove_elems.insert(0, author_selector)
        else:
            self.logger.debug("Could not extract author name")
            author = "{}.ORF.at".format(response.meta["path"])

        for slideshow in response.css(".slideshow"):
            link = response.urljoin(
                slideshow.css('::attr("data-slideshow-json-href")').extract_first()
            ).replace("jsonp", "json")
            slideshow_id = slideshow.css('::attr("id")').extract_first()
            slideshow_response = yield scrapy.Request(link)
            replace_elems["#{}".format(slideshow_id)] = self._create_slideshow_html(
                slideshow_response
            )

        il = FeedEntryItemLoader(
            response=response,
            remove_elems=remove_elems,
            pullup_elems=pullup_elems,
            replace_elems=replace_elems,
            change_attribs=change_attribs,
            change_tags=change_tags,
        )

        # The field is part of a JSON that is sometimes not valid, so don't bother with
        # parsing it properly.
        match = re.search(r'"datePublished": "([^"]+)"', response.text)
        if match:
            # news.ORF.at
            updated = match.group(1)
        else:
            # other
            updated = response.meta["updated"]
        il.add_value("updated", updated)
        il.add_css("title", ".story-lead-headline ::text")  # news
        il.add_css("title", "#ss-storyText > h1 ::text")  # FM4, science
        il.add_value("link", response.url)
        il.add_css("content_html", ".opener img")  # FM4, news
        il.add_css("content_html", ".story-lead-text")  # news
        il.add_css("content_html", "#ss-storyText")
        il.add_css("content_html", "#ss-storyContent")  # news
        il.add_value("author_name", author)
        if author in self._authors:
            il.add_value("path", author)
        il.add_value("path", response.meta["path"])
        il.add_value("category", response.meta["categories"])
        yield il.load_item()

    @staticmethod
    def _create_slideshow_html(response):
        slideshow = json.loads(response.text)
        figures = []
        for photo in slideshow["photos"]:
            url = photo["url"]
            caption = photo.get("description") or ""
            figures.append(
                (
                    '<figure><div><img src="{url}"></div>'
                    + "<figcaption>{caption}</figcaption></figure>"
                ).format(url=url, caption=caption)
            )
        return "<div>" + "".join(figures) + "</div>"

    @staticmethod
    def _extract_author(response):
        domain = urlparse(response.url).netloc
        if domain == "fm4.orf.at":
            author = (
                response.css("#ss-storyText > .socialButtons")
                .xpath(
                    "following-sibling::p[("
                    + "starts-with(., 'Von') or starts-with(., 'von') "
                    + "or starts-with(., 'By') or starts-with(., 'by')"
                    + ") and position() = 1]/a/text()"
                )
                .extract_first()
            )
            author_selector = "#ss-storyText > .socialButtons + p"
            if author:
                return (author.strip(), author_selector)
        elif domain in ["science.orf.at", "help.orf.at", "religion.orf.at"]:
            try:
                author = (
                    response.css("#ss-storyText > p:not(.date):not(.toplink)::text")
                    .extract()[-1]
                    .strip()
                )
                # Possible author string must be in [2, 50].
                if 2 <= len(author) <= 50:
                    # Only take the author name before ",".
                    author = re.split(r"[/,]", author)[0]
                    return (
                        author.strip(),
                        (
                            "#ss-storyText > p:not(.date):not(.toplink):"
                            + "contains('{}')"
                        ).format(author),
                    )
            except IndexError:
                pass
        else:
            author = response.css(".byline ::text").extract_first()
            if author:
                return (re.split(r"[/,]", author)[0].strip(), ".byline")

        return (None, None)

    @staticmethod
    def _get_logo(channel):
        images = {
            "fm4": ("tube", "fm4"),
            "help": ("tube", "help"),
            "science": ("tube", "science"),
            "news": ("news", "news"),
        }
        return (
            "https://tubestatic.orf.at/mojo/1_3/storyserver/{}/{}/images/"
            + "touch-icon-ipad-retina.png"
        ).format(*images.get(channel, images.get("news")))
