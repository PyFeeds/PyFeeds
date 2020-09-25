import json

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class AddendumOrgSpider(FeedsSpider):
    name = "addendum.org"
    start_urls = ["https://www.addendum.org/api/wp/v2/posts"]

    feed_title = "Addendum"
    feed_subtitle = "das, was fehlt"
    feed_link = f"https://www.{name}"
    feed_logo = f"{feed_link}/content/themes/qvv/img/logoAdd.png"
    feed_icon = f"{feed_link}/content/themes/qvv/img/favicons/favicon-16x16.png"

    def parse(self, response):
        posts = json.loads(response.text)
        for post in posts:
            il = FeedEntryItemLoader()
            il.add_value("title", post["title"]["rendered"])
            il.add_value("link", post["link"])
            il.add_value("updated", post["modified"])
            yield scrapy.Request(
                post["link"],
                self._parse_article,
                meta={"il": il},
            )

    def _parse_article(self, response):
        remove_elems = [
            ".article-header .title",
            ".article-header .date",
            ".paragraph-comments-sticky",
            ".qvv-spinner",
            ".article-image.mobile",
            ".image-copyright",
            ".article-image-copyright",
            ".vertical-slider-mobile-image",
            ".quote-box",
            ".icon-end-of-article",
            ".article-teaser-card",
            ".content-row:contains('Lesen Sie auch:')",
            ".article-footer ~ div",
            ".article-footer",
            ".cta-box",
            ".slide-image .mobile",
            ".slide-text .credit",
            ".article-play",
            ".top-tag",
        ]
        change_tags = {
            ".summary": "strong",
            ".article-captioned-image-2": "figure",
            ".keyplayer-card": "figure",
            ".keyplayer-card .text-wrapper": "figcaption",
            ".article-captioned-image": "figure",
            ".article-captioned-image .image-caption": "figcaption",
            ".slide": "figure",
            ".slide-text .caption": "figcaption",
            ".bg-white": "blockquote",
            ".collapse-box": "blockquote",
        }
        il = FeedEntryItemLoader(
            response=response,
            base_url=self.feed_link,
            remove_elems=remove_elems,
            change_tags=change_tags,
            parent=response.meta["il"],
        )
        il.add_css("content_html", ".article-wrapper")
        il.add_css("author_name", ".article-author-link ::text")
        il.add_css("category", ".top-tag ::text")
        yield il.load_item()
