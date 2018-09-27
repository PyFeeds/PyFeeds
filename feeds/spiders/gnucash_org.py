import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsXMLFeedSpider


class GnucashOrgSpider(FeedsXMLFeedSpider):
    name = "gnucash.org"
    start_urls = ["https://www.{}/atom.php".format(name)]

    namespaces = [("atom", "http://www.w3.org/2005/Atom")]
    iterator = "xml"
    itertag = "atom:entry"

    feed_title = "GnuCash News"
    feed_subtitle = (
        "GnuCash is personal and small-business financial-accounting software."
    )
    feed_link = "https://www.{}".format(name)
    feed_icon = "https://www.{}/images/icons/gnc-icon-129x129.png".format(name)
    feed_logo = "https://www.{}/externals/logo_w120.png".format(name)

    def parse_node(self, response, node):
        # Reuse most of the existing fields
        il = FeedEntryItemLoader(selector=node, base_url=self._link)
        il.add_xpath("title", "atom:title/text()")
        il.add_xpath("link", "atom:link/@href")
        il.add_xpath("author_name", "atom:author/atom:name/text()")
        il.add_xpath("author_email", "atom:author/atom:email/text()")
        il.add_xpath("updated", "atom:updated/text()")

        # All news items are stored on a single page and may be referred to via
        # an ID. Extract an item's id and use it to subsequently extract the
        # corresponding news text.
        url, news_id = node.xpath("atom:link/@href").extract_first().split("#")
        return scrapy.Request(
            url, self._parse_news, dont_filter=True, meta={"news_id": news_id, "il": il}
        )

    def _parse_news(self, response):
        il = FeedEntryItemLoader(response=response, parent=response.meta["il"])
        il.add_xpath(
            "content_html",
            '//div[@class="newsheader" and .//a[@id="{}"]]'
            '/following-sibling::div[@class="newsinner"]'.format(
                response.meta["news_id"]
            ),
        )
        return il.load_item()
