import json
import re
from urllib.parse import urlparse

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class OrfAtSpider(FeedsXMLFeedSpider):
    name = "orf.at"
    allowed_domains = ["orf.at"]
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
    # Don't filter duplicates. This would impose a race condition.
    custom_settings = {"DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter"}

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

    def feed_headers(self):
        for channel in self._channels:
            channel_url = "{}.ORF.at".format(channel)
            yield self.generate_feed_header(
                title=channel_url,
                link="https://{}".format(channel_url.lower()),
                path=channel,
                logo=self._get_logo(channel),
            )

    def parse_node(self, response, node):
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
            if any(
                link.startswith(url)
                for url in ["https://debatte.orf.at", "https://iptv.orf.at"]
            ):
                self.logger.debug("Ignoring link to '{}'".format(link))
            else:
                # Sometimes there is a space at the end of a link ...
                yield scrapy.Request(link.strip(), self._parse_article, meta=meta)

    def _parse_article(self, response):
        try:
            # Heuristic for news.ORF.at to to detect teaser articles.
            more = response.css(
                ".story-story p > strong:contains('Mehr') + a::attr(href), "
                + ".story-story p > a:contains('Lesen Sie mehr')::attr(href)"
            ).extract_first()
            if more and more != response.url:
                self.logger.debug(
                    "Detected teaser article, redirecting to {}".format(more)
                )
                yield scrapy.Request(more, self._parse_article, meta=response.meta)
                return
        except IndexError:
            pass

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
            ".slideshow",
            "script",
            ".oon-youtube-logo",
            # redesign
            "#more-to-read-anchor",
            ".social-buttons",
            ".story-horizontal-ad",
            ".linkcard",
        ]
        pullup_elems = {
            ".remote .instagram": 1,
            ".remote .facebook": 1,
            ".remote .twitter": 1,
            ".remote .youtube": 1,
            ".remote table": 1,
        }
        replace_elems = {
            ".remote": "<p><em>Hinweis: Der eingebettete Inhalt ist nur im Artikel "
            + "verfügbar.</em></p>"
        }
        change_attribs = {"img": {"data-src": "src"}}
        author, author_selector = self._extract_author(response)
        if author:
            self.logger.debug("Extracted possible author '{}'".format(author))
            # Remove the paragraph that contains the author.
            remove_elems.insert(0, author_selector)
        else:
            self.logger.debug("Could not extract author name")
            author = "{}.ORF.at".format(response.meta["path"])
        il = FeedEntryItemLoader(
            response=response,
            remove_elems=remove_elems,
            pullup_elems=pullup_elems,
            replace_elems=replace_elems,
            change_attribs=change_attribs,
        )
        # news.ORF.at
        data = response.css('script[type="application/ld+json"]::text').extract_first()
        if data:
            data = json.loads(data)
            updated = data["datePublished"]
        else:
            # other
            updated = response.meta["updated"]
        il.add_value("updated", updated)
        il.add_css("title", "title::text", re="(.*) - .*")
        il.add_value("link", response.url)
        il.add_css("content_html", ".opener img")  # FM4, news
        il.add_css("content_html", ".story-lead-text")  # news
        il.add_css("content_html", "#ss-storyText")
        il.add_css("content_html", "#ss-storyContent")  # news
        il.add_value("author_name", author)
        il.add_value("path", response.meta["path"])
        il.add_value("category", response.meta["categories"])
        yield il.load_item()

    @staticmethod
    def _extract_author(response):
        # Does nothing for Ö3 and Bundesländer. Bundesländer quite seldomly have an
        # author and if they do it's pretty hard to extract reliably.

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
                return (author, author_selector)
        elif domain == "orf.at":
            author = response.css(".byline ::text").extract_first()
            if author:
                return (re.split(r"[/,]", author)[0], ".byline")
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
                        author,
                        (
                            "#ss-storyText > p:not(.date):not(.toplink):"
                            + "contains('{}')"
                        ).format(author),
                    )
            except IndexError:
                pass

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
