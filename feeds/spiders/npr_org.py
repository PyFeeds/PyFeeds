from urllib.parse import urljoin

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider
from feeds.utils import generate_feed_header


class NprOrgSpider(FeedsSpider):
    name = "npr.org"

    _base_url = "https://www.{}".format(name)

    def start_requests(self):
        # Only Planet Money seems to have a public archive.
        newsletters = ["money"]

        for newsletter in newsletters:
            yield scrapy.Request(
                urljoin(self._base_url, "sections/{}/newsletter".format(newsletter)),
                headers={"Cookie": "trackingChoice=true; choiceVersion=1"},
                meta={"dont_cache": True, "path": newsletter},
            )

    def feed_headers(self):
        return []

    def parse(self, response):
        for url in response.css('.item .title a::attr("href")').extract():
            yield scrapy.Request(
                url,
                self._parse_article,
                headers={"Cookie": "trackingChoice=true; choiceVersion=1"},
                meta={"path": response.meta["path"]},
            )

        yield generate_feed_header(
            title="{} Newsletter".format(
                response.css(".branding__image-icon::attr('alt')").extract_first()
            ),
            subtitle=response.css(".branding__mini-teaser ::text").extract_first(),
            link=response.url,
            logo=response.css(".branding__image-icon::attr('src')").extract_first(),
            path=response.meta["path"],
        )

    def _parse_article(self, response):
        def _fix_img_src(elem):
            if "data-original" in elem.attrib:
                elem.attrib["src"] = elem.attrib["data-original"]
            return elem

        remove_elems = [
            ".credit",
            ".hide-caption",
            ".toggle-caption",
            ".enlarge-options",
            ".enlarge_measure",
            ".enlarge_html",
            ".ad-backstage",
            'p:first-of-type:contains("Editor\'s Note: This is an excerpt of")',
            'p:contains("Did you enjoy this newsletter segment?")',
        ]
        replace_elems = {"img": _fix_img_src}
        change_tags = {".image": "figure", ".credit-caption": "figcaption"}

        il = FeedEntryItemLoader(
            response=response,
            base_url=self._base_url,
            remove_elems=remove_elems,
            replace_elems=replace_elems,
            change_tags=change_tags,
        )
        il.add_css("title", "h1 ::text")
        il.add_value("link", response.url)
        il.add_css("content_html", "#storytext")
        il.add_value("path", response.meta["path"])
        il.add_css("updated", '.dateblock time::attr("datetime")')
        il.add_css("author_name", ".byline__name a::text")

        yield il.load_item()
