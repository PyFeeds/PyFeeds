#!/usr/bin/python3

import datetime

import lxml
from lxml.cssselect import CSSSelector
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


def build_tree(text, loader_context):
    base_url = loader_context.get('base_url', None)
    tree = lxml.html.fragment_fromstring(text, create_parent='div',
                                         base_url=base_url)

    # Workaround for https://bugs.launchpad.net/lxml/+bug/1576598.
    # FIXME: Remove this when a workaround is released.
    tree.getroottree().docinfo.URL = base_url

    # Scrapy expects an iterator which it unpacks and feeds to the next
    # function in the pipeline. trees are iterators but we don't want to them
    # to get unpacked so we wrap the tree in another iterator.
    return [tree]


def serialize_tree(tree, in_make_links=False):
    return lxml.html.tostring(tree, encoding='unicode')


def make_links_absolute(tree):
    if tree.base_url:
        # Make references in tags like <a> and <img> absolute.
        tree.make_links_absolute(handle_failures='ignore')
    return [tree]


def cleanup_html(tree, loader_context):
    for css in loader_context.get('css_remove', []):
        selector = CSSSelector(css)
        for elem in selector(tree):
            elem.getparent().remove(elem)

    return [tree]


class BaseItemLoader(ItemLoader):
    # Defaults
    default_output_processor = TakeFirst()

    # Field specific
    id_in = MapCompose(str.strip)

    title_in = MapCompose(str.strip)

    updated_in = MapCompose(str.strip, parse_datetime)

    author_name_in = MapCompose(str.strip)

    author_email_in = MapCompose(str.strip)

    link_in = MapCompose(str.strip)


class FeedItemLoader(BaseItemLoader):
    default_item_class = FeedItem

    # Field specific
    subtitle_in = MapCompose(str.strip)


class FeedEntryItemLoader(BaseItemLoader):
    default_item_class = FeedEntryItem

    # Field specific
    content_text_in = MapCompose(str.strip, remove_tags)
    content_text_out = Join('\n')

    content_html_in = MapCompose(build_tree, cleanup_html,
                                 make_links_absolute, serialize_tree)
    content_html_out = Join()

    enclosure_iri_in = MapCompose(str.strip)

    enclosure_type_in = MapCompose(str.strip)


# Site specific loaders
class CbirdFeedEntryItemLoader(FeedEntryItemLoader):
    content_html_out = Join()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
