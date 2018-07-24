import json
from datetime import datetime, timedelta

from dateutil.tz import gettz
from scrapy import Request

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class TvthekOrfAtSpider(FeedsSpider):
    name = "tvthek.orf.at"
    allowed_domains = ["api-tvthek.orf.at"]
    http_user = "ps_android_v3"
    http_pass = "6a63d4da29c721d4a986fdd31edc9e41"

    _title = "TVthek.ORF.at"
    _subtitle = "ORF TVTHEK"
    _link = "https://tvthek.orf.at"
    _timezone = "Europe/Vienna"

    def start_requests(self):
        # We only parse today and yesterday because at the end of the day this
        # already produces a lot of requests and feed readers cache previous
        # days (i.e. old contents of our feed) anyways.
        # It's not enough to parse only today because we might miss shows that
        # aired just before midnight but were streamed after midnight
        # (see also https://github.com/nblock/feeds/issues/27)
        today = datetime.now(gettz(self._timezone))
        for day in [today, today - timedelta(days=1)]:
            yield Request(
                "https://api-tvthek.orf.at/api/v3/schedule/{}?limit=1000".format(
                    day.strftime("%Y-%m-%d")
                ),
                meta={"dont_cache": True},
            )

    def parse(self, response):
        json_response = json.loads(response.text)

        if "next" in json_response["_links"]:
            yield Request(
                json_response["_links"]["nextPage"], meta={"dont_cache": True}
            )

        for item in json_response["_embedded"]["items"]:
            il = FeedEntryItemLoader(
                response=response, timezone=self._timezone, dayfirst=False
            )
            il.add_value("title", item["title"])
            il.add_value(
                "content_html",
                '<img src="{}">'.format(item["playlist"]["preview_image_url"]),
            )
            if item["description"]:
                il.add_value(
                    "content_html", item["description"].replace("\r\n", "<br>")
                )
            il.add_value("updated", item["date"])
            il.add_value(
                "link", item["url"].replace("api-tvthek.orf.at", "tvthek.orf.at")
            )
            yield Request(
                item["_links"]["profile"]["href"],
                self._parse_profile,
                meta={"item": il},
                dont_filter=True,
            )

    def _parse_profile(self, response):
        il = response.meta["item"]
        profile = json.loads(response.text)
        il.add_value(
            "category", self._categories_from_oewa_base_path(profile["oewa_base_path"])
        )
        yield il.load_item()

    def _categories_from_oewa_base_path(self, oewa_base_path):
        """Parse ÖWA Base Path into a list of categories.

         Base paths look like this:

           * RedCont/KulturUndFreizeit/FilmUndKino
           * RedCont/KulturUndFreizeit/Sonstiges
           * RedCont/Lifestyle/EssenUndTrinken
           * RedCont/Nachrichten/Nachrichtenueberblick
           * RedCont/Sport/Sonstiges
        """
        old_new = {
            "RedCont": "",
            "Sonstiges": "",
            "Und": " und ",
            "ue": "ü",
            "ae": "ä",
            "oe": "ö",
            "Ue": "Ü",
            "Ae": "Ä",
            "Oe": "Ö",
        }
        for old, new in old_new.items():
            oewa_base_path = oewa_base_path.replace(old, new)
        return filter(lambda x: x != "", oewa_base_path.split("/"))
