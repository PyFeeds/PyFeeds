import scrapy
from scrapy.http import HtmlResponse

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class WienerLinienAtSpider(FeedsSpider):
    name = "wienerlinien.at"
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html",
            # Don't include Accept-Language so the datetime in the HTML
            # response includes the time.
        }
    }
    start_urls = [
        "https://www.wienerlinien.at/eportal3/ep/scrollingListView.do?"
        "scrolling=true&startIndex=0&channelId=-47186&programId=74577"
    ]

    feed_title = "Wiener Linien"
    feed_subtitle = "Aktuelle Meldungen"

    def parse(self, response):
        # Wiener Linien returns HTML with an XML content type which creates an
        # XmlResponse.
        response = HtmlResponse(url=response.url, body=response.body)
        for item in response.css(".block-news-item"):
            il = FeedEntryItemLoader(
                response=response,
                timezone="Europe/Vienna",
                ignoretz=True,
                base_url="https://www.{}".format(self.name),
            )
            link = response.urljoin(item.css("a::attr(href)").extract_first())
            il.add_value("link", link)
            il.add_value("title", item.css("h3::text").extract_first())
            il.add_value("updated", item.css(".date::text").extract_first())
            yield scrapy.Request(link, self.parse_item, meta={"il": il})

    def parse_item(self, response):
        remove_elems = ["h1", ".delayed-image-load"]
        change_tags = {"noscript": "div"}
        il = FeedEntryItemLoader(
            response=response,
            parent=response.meta["il"],
            remove_elems=remove_elems,
            change_tags=change_tags,
            base_url="https://www.{}".format(self.name),
        )
        il.add_xpath("content_html", '//div[@id="main-inner"]')
        return il.load_item()
