import scrapy

from feeds.spiders import FeedsXMLFeedSpider, kurier_at


class ProfilAtSpider(FeedsXMLFeedSpider):
    name = "profil.at"
    itertag = "item/link/text()"
    iterator = "xml"
    start_urls = ["https://www.profil.at/xml/rss"]

    feed_title = "PROFIL"
    feed_subtitle = "Österreichs unabhängiges Nachrichtenmagazin"

    def parse_node(self, response, node):
        path = node.extract().replace("https://profil.at/", "")
        url = "https://efs.profil.at/api/v1/cfs/route?uri=/profilat/" + path
        return scrapy.Request(
            url, kurier_at.parse_article, meta={"feed_type": "article"}
        )
