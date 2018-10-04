import re

from scrapy.selector import Selector
from scrapy.loader.processors import TakeFirst
import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class TuWienAcAtSpider(FeedsSpider):
    name = "tuwien.ac.at"

    feed_title = "TU Wien: Mitteilungsblätter"
    feed_icon = "https://{}/favicon.ico".format(name)

    def start_requests(self):
        yield scrapy.Request(
            "https://tiss.{}/mbl/main/uebersicht".format(self.name),
            headers={"Accept-Language": "de-DE,de"},
            meta={"dont_cache": True},
        )

    def parse(self, response):
        mitteilungsblaetter = response.css(".mitteilungsblaetter")
        updated = mitteilungsblaetter.css("::text").re_first("(\d{2}\.\d{2}\.\d{4})")
        link = response.urljoin(
            mitteilungsblaetter.css('a::attr("href")').extract_first()
        )
        return scrapy.Request(
            response.urljoin(link),
            self._parse_mitteilungsblatt,
            meta={"updated": updated},
        )

    def _parse_mitteilungsblatt(self, response):
        content = "".join(response.css("#contentInner > div").extract())
        for entry in re.split('<a name="n\d*">', content)[1:]:
            entry = Selector(text=entry)
            il = FeedEntryItemLoader(
                selector=entry,
                base_url="https://tiss.{}".format(self.name),
                timezone="Europe/Vienna",
                dayfirst=True,
            )
            il.add_value("updated", response.meta["updated"])
            anchor_name = entry.css('::attr("name")').extract_first()
            il.add_value("link", response.url + "#{}".format(anchor_name))
            il.add_css("title", "strong > u ::text", TakeFirst())
            il.add_css("content_html", "p")
            yield il.load_item()
