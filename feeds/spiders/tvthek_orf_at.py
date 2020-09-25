import json
from datetime import datetime, timedelta

from dateutil.tz import gettz
from scrapy import Request

from feeds.exceptions import DropResponse
from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class TvthekOrfAtSpider(FeedsSpider):
    name = "tvthek.orf.at"
    http_user = "ps_android_v3"
    http_pass = "6a63d4da29c721d4a986fdd31edc9e41"

    feed_title = "TVthek.ORF.at"
    feed_subtitle = "ORF TVTHEK"
    feed_link = "https://tvthek.orf.at"

    def start_requests(self):
        # We only parse today and yesterday because at the end of the day this
        # already produces a lot of requests and feed readers cache previous
        # days (i.e. old contents of our feed) anyways.
        # It's not enough to parse only today because we might miss shows that
        # aired just before midnight but were streamed after midnight
        # (see also https://github.com/nblock/feeds/issues/27)
        today = datetime.now(gettz("Europe/Vienna"))
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
            # Skip incomplete items or items with active youth protection.
            # We want to have working download links in the feed item.
            if not item["segments_complete"] or item["has_active_youth_protection"]:
                continue

            # We scrape the episode itself so we can get the segments which are not
            # embedded in the schedule response.
            # Furthermore since this request will be cached, the download URL will also
            # be cached which is convenient for youth protected content.
            yield Request(
                item["_links"]["self"]["href"],
                self._parse_episode,
                # Responses are > 100 KB and useless after 7 days.
                # So don't keep them longer than necessary.
                meta={"cache_expires": timedelta(days=7)},
            )

    def _parse_episode(self, response):
        item = json.loads(response.text)
        il = FeedEntryItemLoader()
        il.add_value("title", item["title"])
        il.add_value(
            "content_html",
            '<img src="{}">'.format(item["playlist"]["preview_image_url"]),
        )
        if item["description"]:
            il.add_value("content_html", item["description"].replace("\r\n", "<br>"))
        il.add_value("updated", item["date"])
        il.add_value("link", item["url"].replace("api-tvthek.orf.at", "tvthek.orf.at"))
        # Check how many segments are part of this episode.
        if len(item["_embedded"]["segments"]) == 1:
            # If only one segment, item["sources"] contains invalid links.
            # We use the first embedded segment instead.
            # This is also how mediathekviewweb.de works.
            item["sources"] = item["_embedded"]["segments"][0]["sources"]
        try:
            video = next(
                s
                for s in item["sources"]["progressive_download"]
                if s["quality_key"] == "Q8C"
            )
            il.add_value("enclosure", {"iri": video["src"], "type": "video/mp4"})
        except StopIteration:
            self.logger.warning(
                "Could not extract video for '{}'!".format(item["title"])
            )
            raise DropResponse(
                "Skipping {} because not downloadable yet".format(response.url),
                transient=True,
            )

        subtitle = item["_embedded"].get("subtitle")
        if subtitle:
            subtitle = subtitle["_embedded"]["srt_file"]["public_urls"]["reference"]
            il.add_value("enclosure", {"iri": subtitle["url"], "type": "text/plain"})
        else:
            self.logger.debug("No subtitle file found for '{}'".format(item["url"]))
        il.add_value(
            "category",
            self._categories_from_oewa_base_path(
                item["_embedded"]["profile"]["oewa_base_path"]
            ),
        )
        return il.load_item()

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
