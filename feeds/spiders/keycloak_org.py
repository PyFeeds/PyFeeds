import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class KeycloakOrgSpider(FeedsSpider):
    name = "keycloak.org"
    allowed_domains = [name]
    start_urls = [f"https://www.{name}/blog-archive.html"]

    feed_title = "Keycloak"
    feed_subtitle = "Recent blog posts from Keycloak"
    feed_link = f"https://www.{name}/blog"
    feed_icon = f"https://www.{name}/resources/favicon.ico"
    feed_logo = f"https://www.{name}/resources/images/keycloak_logo_200px.svg"

    def parse(self, response):
        for url in response.css("div.kc-article ul li a::attr('href')").getall():
            yield scrapy.Request(response.urljoin(url), self.parse_article)

    def parse_article(self, response):
        il = FeedEntryItemLoader(
            selector=response.css("div.kc-article"),
            timezone="Europe/Vienna",
            remove_elems=["h1", "p.blog-date", "div.alert-warning"],
        )
        il.add_css("title", "h1::text")
        il.add_value("link", response.url)
        il.add_css("updated", "p.blog-date::text", re=r"^(.*\d{4})")
        il.add_css("author_name", "p.blog-date::text", re=r"by (.*)$")
        il.add_css("content_html", "div.kc-article")
        return il.load_item()
