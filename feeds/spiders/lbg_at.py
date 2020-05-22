import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class LbgAtSpider(FeedsSpider):
    name = "lbg.at"
    allowed_domains = [name]
    start_urls = [
        f"https://www.{name}/steuerberater_wirtschaftspruefer_unternehmensberater_"
        + "oesterreich/mobile_ger.html"
    ]

    feed_title = "LBG"
    feed_subtitle = "Steuer- und Unternehmernews"
    feed_link = f"https://www.{name}"
    feed_icon = f"{feed_link}/static/common/images/favicon.ico"
    feed_logo = f"{feed_link}/static/common/images/logo.gif"

    def parse(self, response):
        for url in response.css("section#e213794 a::attr('href')").getall():
            yield scrapy.Request(url, self.parse_article)

    def parse_article(self, response):
        il = FeedEntryItemLoader(
            selector=response.css("article.news_article"),
            timezone="Europe/Vienna",
            remove_elems=["h1", "p.date", "footer"],
            remove_elems_xpath=[
                "//p[starts-with(text(), 'Stand: ')]",
                "//strong[starts-with(text(), 'Kontakt ')]/ancestor::p",
                "//strong[starts-with(text(), 'LBG - ')]/ancestor::p",
                "//strong[starts-with(text(), '© LBG')]/ancestor::p",
                "//p[starts-with(text(), 'Wir beraten eine große Vielfalt an Branch')]",
                "//p[starts-with(text(), 'Im Beratungsfeld „Personalverrechnung, Lo')]",
            ],
        )
        il.add_value("link", response.url.replace("/index_ger.html", ""))
        il.add_css("title", "h1::text")
        il.add_css("updated", "p.date::text")
        il.add_css("content_html", "article.news_article")
        yield il.load_item()
