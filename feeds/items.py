#!/usr/bin/python3

import scrapy


class BaseItem(scrapy.Item):
    # Required date format: RFC 3339
    UPDATED_FMT = '%Y-%m-%dT%H:%M:%SZ'

    # Required
    # The feed/entry id. It may be auto generated in case a link is present.
    id = scrapy.Field()

    # The feed/entry title.
    title = scrapy.Field()

    # The last updated date of the feed as datetime object.
    updated = scrapy.Field(
        serializer=lambda x: x.strftime(BaseItem.UPDATED_FMT))

    # Recommended
    # Must be a dict containing at least 'name' and optionally 'email'.
    author = scrapy.Field()

    # A unique link to a feed/item.
    link = scrapy.Field()


class FeedItem(BaseItem):
    # Optional
    subtitle = scrapy.Field()


class FeedEntryItem(BaseItem):
    # Recommended
    content_text = scrapy.Field()
    content_html = scrapy.Field()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
