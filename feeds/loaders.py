#!/usr/bin/python3

import datetime
import pytz

from scrapy.loader import ItemLoader
from scrapy.loader.processors import Join
from scrapy.loader.processors import MapCompose
from scrapy.loader.processors import TakeFirst
from w3lib.html import remove_tags

from feeds.items import FeedItem
from feeds.items import FeedEntryItem


def parse_datetime(text, loader_context):
    datetime_format = loader_context.get('datetime_format', '%d.%m.%Y')
    timezone = loader_context.get('timezone', pytz.UTC)
    try:
        return (timezone.localize(datetime.datetime.strptime(text,
                datetime_format)).astimezone(pytz.UTC))
    except ValueError:
        return None


class BaseItemLoader(ItemLoader):
    # Defaults
    default_output_processor = TakeFirst()

    # Field specific
    id_in = MapCompose(str.strip)

    title_in = MapCompose(str.strip, str.title)

    updated_in = MapCompose(str.strip, parse_datetime)

    author_name_in = MapCompose(str.strip)

    author_email_in = MapCompose(str.strip)

    link_in = MapCompose(str.strip)


class FeedItemLoader(BaseItemLoader):
    default_item_class = FeedItem

    # Field specific
    subtitle_in = MapCompose(str.strip, str.title)


class FeedEntryItemLoader(BaseItemLoader):
    default_item_class = FeedEntryItem

    # Field specific
    content_text_in = MapCompose(str.strip, remove_tags)
    content_text_out = Join('\n')

    content_html_in = MapCompose(str.strip)
    content_html_out = Join('<br>')


# Site specific loaders
class CbirdFeedEntryItemLoader(FeedEntryItemLoader):
    content_html_out = Join()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
