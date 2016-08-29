#!/usr/bin/python3

import scrapy


class BaseItem(scrapy.Item):
    # Required date format: RFC 3339 (ISO 8601 extended format)
    UPDATED_FMT = 'Y-MM-ddTHH:mm:ssZZZZZ'

    # Required
    # The feed/entry id. It may be auto generated in case a link is present.
    id = scrapy.Field()

    # The feed/entry title.
    title = scrapy.Field()

    # The last updated date of the feed as Delorean object.
    updated = scrapy.Field(
        serializer=lambda x: x.format_datetime(BaseItem.UPDATED_FMT))

    # Recommended
    author_name = scrapy.Field()
    author_email = scrapy.Field()

    # A unique link to a feed/item.
    link = scrapy.Field()

    # Optional
    category = scrapy.Field()

    # Optional
    path = scrapy.Field()


class FeedItem(BaseItem):
    # Optional
    subtitle = scrapy.Field()

    # Optional
    icon = scrapy.Field()

    # Optional
    logo = scrapy.Field()


class FeedEntryItem(BaseItem):
    # Recommended
    content_text = scrapy.Field()
    content_html = scrapy.Field()

    # Optional
    enclosure_iri = scrapy.Field()
    # Optional
    enclosure_type = scrapy.Field()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
