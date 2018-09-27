import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class IndieHackersComSpider(FeedsSpider):
    name = "indiehackers.com"
    allowed_domains = [name]
    start_urls = ["https://www.indiehackers.com/interviews/page/1"]

    feed_title = "Indie Hackers"

    def parse(self, response):
        interviews = response.css(
            ".interview__link::attr(href), .interview__date::text"
        ).extract()
        self._logo = response.urljoin(
            response.css(
                'link[rel="icon"][sizes="192x192"]::attr(href)'
            ).extract_first()
        )
        self._icon = response.urljoin(
            response.css('link[rel="icon"][sizes="16x16"]::attr(href)').extract_first()
        )
        for link, date in zip(interviews[::2], interviews[1::2]):
            yield scrapy.Request(
                response.urljoin(link),
                self._parse_interview,
                meta={"updated": date.strip()},
            )

    def _parse_interview(self, response):
        remove_elems = [
            ".shareable-quote",
            ".share-bar",
            # Remove the last two h2s and all paragraphs below.
            ".interview-body > h2:last-of-type ~ p",
            ".interview-body > h2:last-of-type",
            ".interview-body > h2:last-of-type ~ p",
            ".interview-body > h2:last-of-type",
        ]
        il = FeedEntryItemLoader(
            response=response,
            base_url="https://{}".format(self.name),
            remove_elems=remove_elems,
        )
        il.add_value("link", response.url)
        il.add_css("title", "h1::text")
        il.add_css("author_name", "header .user-link__name::text")
        il.add_css("content_html", ".interview-body")
        il.add_value("updated", response.meta["updated"])
        yield il.load_item()
