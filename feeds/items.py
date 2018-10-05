from datetime import timezone

import scrapy


def to_rfc3339(date_time):
    """Return RFC 3339 representation of date_time with timezone UTC."""
    # Shifting to UTC and hardcoding "Z" for the timezone is a cheap way to get a
    # RFC 3339 compliant timestamp.
    return date_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class BaseItem(scrapy.Item):
    # Required
    # The feed/entry id. It may be auto generated in case a link is present.
    id = scrapy.Field()

    # The feed/entry title.
    title = scrapy.Field()

    # The last updated date of the feed.
    # Required date format: RFC 3339 (ISO 8601 extended format)
    updated = scrapy.Field(serializer=to_rfc3339)

    # Recommended
    author_name = scrapy.Field()
    author_email = scrapy.Field()

    # A unique link to a site/item.
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

    # Optional
    link_self = scrapy.Field()


class FeedEntryItem(BaseItem):
    # Recommended
    content_text = scrapy.Field()
    content_html = scrapy.Field()

    # Optional
    enclosure = scrapy.Field()
