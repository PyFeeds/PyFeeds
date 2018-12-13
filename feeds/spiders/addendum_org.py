import json
from copy import deepcopy
from functools import partial

import lxml
import scrapy
from inline_requests import inline_requests

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider
from feeds.utils import generate_feed_header


class AddendumOrgSpider(FeedsXMLFeedSpider):
    name = "addendum.org"
    start_urls = ["https://www.addendum.org/feed/rss2-addendum"]

    _max_articles = 10
    _num_articles = 0

    def feed_headers(self):
        feeds = {"": "Addendum", "podcast": "Addendum Podcast"}
        for path, title in feeds.items():
            yield generate_feed_header(
                title=title,
                path=path,
                subtitle="das, was fehlt",
                link="https://www.{}".format(self.name),
                icon=(
                    "https://www.{}/resources/dist/favicons/android-chrome-192x192.png"
                ).format(self.name),
            )

    def parse_node(self, response, node):
        url = node.xpath("link/text()").extract_first()
        if not node.xpath("category"):
            # Overview pages don't have a category.
            return
        if self._num_articles >= self._max_articles:
            # Maximum number of articles reached.
            return
        self._num_articles += 1
        return scrapy.Request(url, self._parse_article)

    @staticmethod
    def _build_api_request(video_id):
        return scrapy.Request(
            "https://edge.api.brightcove.com/playback/v1/accounts/5548093587001/"
            + "videos/{}".format(video_id),
            headers={
                "Accept": "application/json;pk="
                + "BCpkADawqM0FoC-KqFQHZMCJQrN5XC_gdWIYO4204LOOSFrv34GdVavc7TJP"
                + "tw5F612ztVUZmw47U2kWmyVU3kdtE6dga_P110le86FuaNCGPYlJ6ljW0Z3_"
                + "HYTlnFsPeFs8F61PGWYBsYnG"
            },
        )

    @inline_requests
    def _parse_article(self, response):
        def _inline_video(videos, elem):
            if "data-video-id" in elem.attrib:
                source = lxml.etree.Element("source")
                source.attrib["src"] = videos[elem.attrib["data-video-id"]]
                source.attrib["type"] = "video/mp4"
                elem.insert(0, source)
                return elem
            else:
                # Header video, replace with placeholder image.
                parent = elem.getparent()
                parent.tag = "figure"
                if "data-placeholderbig" in elem.attrib:
                    src = elem.attrib["data-placeholderbig"]
                else:
                    src = elem.attrib["data-placeholder"]
                image = lxml.etree.Element("img")
                image.attrib["src"] = src
                return image

        def _inline_picture(elem):
            elem.tag = "img"
            src = elem.attrib.get("data-original")
            data_min_width = 1000 if src else -1
            for child in elem.getchildren():
                if child.tag != "span":
                    continue
                if int(child.attrib.get("data-min-width", 0)) > data_min_width:
                    src = child.attrib["data-src"]
                    data_min_width = int(child.attrib.get("data-min-width", 0))
                child.drop_tree()
            elem.attrib["src"] = src
            return elem

        audio_ids = response.css(
            '#BCaudioPlayer_eindeutig::attr("data-video-id")'
        ).extract()
        video_ids = response.css('.video-js::attr("data-video-id")').extract()
        media = {}
        for media_id in audio_ids + video_ids:
            api_response = yield self._build_api_request(media_id)
            api_response = json.loads(api_response.text)
            media[media_id] = sorted(
                (
                    video
                    for video in api_response["sources"]
                    if "src" in video and video.get("container") == "MP4"
                ),
                key=lambda v: v["size"],
            )[-1]["src"]

        remove_elems = [
            "h1",
            "script",
            "style",
            ".projectNav",
            ".socialShare",
            ".socialShare__headline",
            ".socialShare__icon",
            ".socialMedia",
            ".socialMedia__headline",
            ".whyRead",
            ".overlayCTA",
            ".authors",
            ".sectionBackground--colorTheme1",
            ".heroStage__copyright",
            ".heroStage__downLink",
            ".callToAction",
            ".print-action",
            ".internalLink span",
            ".addCommunity",
            ".download",
            ".BCaudioPlayer",
            ".icon-date",
            ".callToAction__button",
            'a[href^="http://partners.webmasterplan.com/click.asp"]',
            ".relatedSlider",
            ".imageLightbox",
            ".image__copyrightWrapper",
            ".image__zoom",
            ".image > .picture",
            ".imageHC",
        ]
        change_tags = {
            "div.heroStage__introText": "strong",
            ".quote": "blockquote",
            ".quote__label": "footer",
            ".supernumber": "blockquote",
            ".image": "figure",
            ".image__element": "div",
        }
        replace_elems = {
            "video": partial(_inline_video, media),
            ".picture": _inline_picture,
        }
        pullup_elems = {".image__content figcaption": 3}
        il = FeedEntryItemLoader(
            response=response,
            base_url=response.url,
            remove_elems=remove_elems,
            change_tags=change_tags,
            replace_elems=replace_elems,
            pullup_elems=pullup_elems,
        )
        il.add_value("link", response.url)
        il.add_css("author_name", ".sidebar .authors__name::text")
        il.add_css("title", "title::text", re="(.*) - Addendum")
        il.add_css("updated", 'meta[property="article:modified_time"]::attr(content)')
        # If not yet modified:
        il.add_css("updated", 'meta[property="article:published_time"]::attr(content)')
        il.add_css("content_html", ".content")
        for medium_id, medium_url in media.items():
            if medium_id not in audio_ids:
                il.add_value("enclosure", {"iri": medium_url, "type": "video/mp4"})
        item = il.load_item()
        # Save a copy before yielding it.
        item_podcast = deepcopy(item)
        yield item

        if audio_ids:
            # Export to podcast feed.
            il = FeedEntryItemLoader(item=item_podcast)
            il.add_value("path", "podcast")
            for medium_id, medium_url in media.items():
                if medium_id in audio_ids:
                    il.add_value("enclosure", {"iri": medium_url, "type": "audio/mp4"})
            yield il.load_item()
