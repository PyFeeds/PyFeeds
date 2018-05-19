from datetime import datetime
import html
import os
import re

from lxml import etree
from lxml.cssselect import CSSSelector
from lxml.html import HtmlComment
from scrapy.loader import ItemLoader
from scrapy.loader.processors import Compose
from scrapy.loader.processors import Identity
from scrapy.loader.processors import Join
from scrapy.loader.processors import MapCompose
from scrapy.loader.processors import TakeFirst
from w3lib.html import remove_tags
import delorean
import dateparser
import lxml

from feeds.items import FeedItem
from feeds.items import FeedEntryItem


def parse_datetime(text, loader_context):
    if isinstance(text, datetime):
        return delorean.Delorean(text, timezone=loader_context.get("timezone", "UTC"))
    elif isinstance(text, str):
        try:
            return delorean.parse(
                text.strip(),
                timezone=loader_context.get("timezone", "UTC"),
                dayfirst=loader_context.get("dayfirst", False),
                yearfirst=loader_context.get("yearfirst", True),
            ).shift("UTC")
        except ValueError:
            return delorean.Delorean(
                dateparser.parse(text), timezone=loader_context.get("timezone", "UTC")
            )
    else:
        return text


def replace_regex(text, loader_context):
    for pattern, repl in loader_context.get("replace_regex", {}).items():
        text = re.sub(pattern, repl, text)

    return text


def build_tree(text, loader_context):
    base_url = loader_context.get("base_url", None)
    tree = lxml.html.fragment_fromstring(text, create_parent="div", base_url=base_url)

    # Workaround for https://bugs.launchpad.net/lxml/+bug/1576598.
    # FIXME: Remove this when a workaround is released.
    tree.getroottree().docinfo.URL = base_url

    # Scrapy expects an iterator which it unpacks and feeds to the next
    # function in the pipeline. trees are iterators but we don't want to them
    # to get unpacked so we wrap the tree in another iterator.
    return [tree]


def serialize_tree(tree, in_make_links=False):
    return lxml.html.tostring(tree, encoding="unicode")


def make_links_absolute(tree):
    if tree.base_url:
        # Make references in tags like <a> and <img> absolute.
        tree.make_links_absolute(handle_failures="ignore")
    return [tree]


def cleanup_html(tree, loader_context):
    # Remove tags.
    for elem_sel in loader_context.get("remove_elems", []):
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            elem.getparent().remove(elem)

    for elem_sel in loader_context.get("remove_elems_xpath", []):
        for elem in tree.xpath(elem_sel):
            elem.getparent().remove(elem)

    # Change tag names.
    for elem_sel, elem_tag in loader_context.get("change_tags", {}).items():
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            elem.tag = elem_tag

    # tree.iter() iterates over the tree including the root node.
    for elem in tree.iter():
        # Remove HTML comments.
        if isinstance(elem, HtmlComment):
            elem.getparent().remove(elem)
        # Remove class and id attribute from all elements which are not needed
        # in the feed.
        elem.attrib.pop("class", None)
        elem.attrib.pop("id", None)
        # Delete data- attributes that have no general meaning.
        for attrib in list(elem.attrib.keys()):
            if attrib.startswith("data-"):
                elem.attrib.pop(attrib)

    return [tree]


def convert_footnotes(tree, loader_context):
    footnotes = []

    # Convert footnotes.
    for elem_sel in loader_context.get("convert_footnotes", []):
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            footnotes.append(elem.text_content())
            ref = etree.Element("span")
            ref.text = " [{}]".format(len(footnotes))
            elem.getparent().replace(elem, ref)

    # Add new <div> with all the footnotes, one per <p>
    if footnotes:
        footnotes_elem = etree.Element("div")
        tree.append(footnotes_elem)

    for i, footnote in enumerate(footnotes):
        footnote_elem = etree.Element("p")
        footnote_elem.text = "[{}] {}".format(i + 1, footnote)
        footnotes_elem.append(footnote_elem)

    return [tree]


def skip_empty_tree(tree):
    if tree.text:
        # Has a text.
        return [tree]

    if len(tree):
        # Has children.
        return [tree]

    return None


def skip_false(value):
    """
    Skip values that evaluate to False.

    Scrapy only skips values that are None by default. In feeds we want to
    tighten that policy and also skip empty strings, False and everything else
    that evaluates to False.
    """
    if value:
        return value

    return None


class BaseItemLoader(ItemLoader):
    # Defaults
    # Unescape twice to get rid of &amp;&xxx; encoding errors.
    default_input_processor = MapCompose(
        skip_false, str.strip, html.unescape, html.unescape
    )
    default_output_processor = TakeFirst()

    # Join first two elements on ": " and the rest on " - ".
    title_out = Compose(lambda t: [": ".join(t[:2])] + t[2:], Join(" - "))

    updated_in = MapCompose(skip_false, parse_datetime)

    author_name_out = Join(", ")

    # Optional
    path_out = Join(os.sep)


class FeedItemLoader(BaseItemLoader):
    default_item_class = FeedItem


class FeedEntryItemLoader(BaseItemLoader):
    default_item_class = FeedEntryItem

    # Field specific
    content_text_in = MapCompose(skip_false, str.strip, remove_tags)
    content_text_out = Join("\n")

    content_html_in = MapCompose(
        skip_false,
        replace_regex,
        build_tree,
        convert_footnotes,
        cleanup_html,
        skip_empty_tree,
        make_links_absolute,
        serialize_tree,
    )
    content_html_out = Join()

    category_out = Identity()


# Site specific loaders
class CbirdFeedEntryItemLoader(FeedEntryItemLoader):
    content_html_out = Join()


# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
