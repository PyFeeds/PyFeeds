import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class UsenixOrgSpider(FeedsSpider):
    name = "usenix.org"
    start_urls = ["https://www.usenix.org/publications/loginonline"]

    feed_title = ";login: online"
    feed_subtitle = "An open access publication driven by the USENIX community"
    feed_link = start_urls[0]
    feed_logo = f"https://{name}/sites/all/themes/custom/cotija/images/logo.svg"
    path = "loginonline"

    def parse(self, response):
        # Find articles on the first page. Ignore additional pages.
        for article in response.css(".view-content a::attr(href)").extract():
            yield scrapy.Request(response.urljoin(article), self.parse_article)

    def parse_article(self, response):
        il = FeedEntryItemLoader(response=response, base_url=self.start_urls[0])
        il.add_value("link", response.url)
        il.add_css("title", 'meta[property="og:title"]::attr(content)')
        il.add_css("updated", 'meta[property="article:modified_time"]::attr(content)')
        il.add_css("author_name", ".field-pseudo-field--author-list a::text")
        il.add_css("category", ".field-type-taxonomy-term-reference .field-item::text")
        il.add_css("content_html", ".paragraphs-items-full")
        il.add_value("path", self.path)
        return il.load_item()
