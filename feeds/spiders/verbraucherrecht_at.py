import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class VerbraucherrechtAtSpider(FeedsSpider):
    name = "verbraucherrecht.at"
    start_urls = [f"https://{name}/aktuelle-news/5202"]

    feed_title = "Verbraucherrecht"
    feed_subtitle = "Neuigkeiten rund um Konsumentenschutz und Verbraucherrechte"
    feed_author_name = "Verein für Konsumenteninformation"
    feed_link = f"https://{name}"
    feed_icon = f"https://{name}/themes/custom/wdm/images/favicon/favicon-vki.ico"
    feed_logo = f"https://{name}/themes/custom/wdm/images/logo/logo-vki-verbraucherrecht.svg"  # noqa

    def parse(self, response):
        # Fetch only the current news page and deliberately ignore old news.
        for url in response.css("div.view-content a::attr('href')").getall():
            yield scrapy.Request(url, self.parse_article)

    def parse_article(self, response):
        il = FeedEntryItemLoader(
            selector=response.css("div.content"),
            timezone="Europe/Vienna",
            remove_elems=["div.wrap>h1", "div#article-stat"],
            dayfirst=True,
            yearfirst=False,
        )
        il.add_css("title", "h1::text")
        il.add_value("link", response.url)
        il.add_css("updated", "time::attr('datetime')")
        il.add_css("content_html", "div.content")
        return il.load_item()
