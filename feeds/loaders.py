import html
import logging
import re
from copy import deepcopy
from datetime import datetime
from textwrap import TextWrapper
from urllib.parse import quote_plus as urlquote_plus
from urllib.parse import urljoin

import dateparser
import lxml
from dateutil.parser import parse as dateutil_parse
from dateutil.tz import gettz
from itemloaders.processors import Compose, Identity, Join, MapCompose, TakeFirst
from lxml.cssselect import CSSSelector
from lxml.html.clean import Cleaner
from scrapy.loader import ItemLoader
from w3lib.html import remove_tags

from feeds.items import FeedEntryItem, FeedItem
from feeds.settings import get_feeds_settings

logger = logging.getLogger(__name__)

# List of so-called empty elements in HTML.
# Source: https://developer.mozilla.org/en-US/docs/Glossary/Empty_element
EMPTY_ELEMENTS = [
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]


def parse_datetime(date_time, loader_context):
    if isinstance(date_time, datetime):
        return date_time
    elif isinstance(date_time, str):
        try:
            return dateutil_parse(
                date_time.strip(),
                dayfirst=loader_context.get("dayfirst", False),
                yearfirst=loader_context.get("yearfirst", True),
                ignoretz=loader_context.get("ignoretz", False),
            )
        except ValueError:
            # If dateutil can't parse it, it might be a human-readable date.
            return dateparser.parse(date_time)
    else:
        raise ValueError("date_time must be datetime or a str.")


def apply_timezone(date_time, loader_context):
    if not date_time.tzinfo:
        # If date_time object is not aware, apply timezone from loader_context.
        # In case a timezone is not supplied, just assume UTC.
        date_time = date_time.replace(
            tzinfo=gettz(loader_context.get("timezone", "UTC"))
        )
    return date_time


def replace_regex(text, loader_context):
    for pattern, repl in loader_context.get("replace_regex", {}).items():
        text = re.sub(pattern, repl, text)

    return text


def build_tree(text, loader_context=None):
    base_url = loader_context.get("base_url", None) if loader_context else None
    tree = lxml.html.fragment_fromstring(text, create_parent="div", base_url=base_url)

    if base_url:
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


def make_srcset_absolute(tree):
    # Also make URLs in srcset attributes absolute (not part of make_links_absolute()).
    if tree.base_url:
        # https://html.spec.whatwg.org/multipage/images.html#srcset-attributes
        srcset_regex = re.compile(
            r"(?:\s*(?P<url>[^\s,]+)\s*(?P<dimension> \d+w| \d+x)\s*(?:,|$))"
        )
        selector = CSSSelector("img[srcset]")
        for elem in selector(tree):
            srcset = []
            for url, dimension in srcset_regex.findall(elem.attrib["srcset"]):
                srcset.append(urljoin(tree.base_url, url) + dimension)
            elem.attrib["srcset"] = ",".join(srcset)

    return [tree]


def pullup_elems(tree, loader_context):
    for elem_child, parent_dist in loader_context.get("pullup_elems", {}).items():
        selector = CSSSelector(elem_child)
        for elem in selector(tree):
            parent = elem
            for _ in range(parent_dist):
                parent = parent.getparent()
            if parent is not None and parent.getparent() is not None:
                elem.tail = parent.tail
                parent.getparent().replace(parent, elem)
            else:
                logger.error(
                    'Could not find parent with distance {} for selector "{}".'.format(
                        parent_dist, elem_child
                    )
                )

    return [tree]


def replace_elems(tree, loader_context):
    for elem_sel, elem_repl in loader_context.get("replace_elems", {}).items():
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            # If elem_repl is callable, call it to create a new element (or just modify
            # the old one).
            if callable(elem_repl):
                elem_new = elem_repl(elem)
            else:
                elem_new = elem_repl

            # The new element is None, just remove the old one.
            if elem_new is None:
                elem.drop_tree()
            else:
                if isinstance(elem_new, str):
                    # The new element is a string, create a proper element out of it.
                    elem_new = lxml.html.fragment_fromstring(elem_new)
                else:
                    # Create a copy of elem_new in case the element should be used as a
                    # replacement more than once.
                    elem_new = deepcopy(elem_new)
                # Take care to preserve the tail of the old element.
                elem_new.tail = elem.tail
                elem.getparent().replace(elem, elem_new)

    return [tree]


def remove_elems(tree, loader_context):
    remove_elems = []

    settings = get_feeds_settings()
    remove_images = settings.getbool("FEEDS_CONFIG_REMOVE_IMAGES")
    if remove_images:
        remove_elems += ["img"]

    # Remove tags.
    for elem_sel in loader_context.get("remove_elems", []) + remove_elems:
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            elem.drop_tree()

    for elem_sel in loader_context.get("remove_elems_xpath", []):
        for elem in tree.xpath(elem_sel):
            elem.drop_tree()

    return [tree]


def change_attribs(tree, loader_context):
    # Change attrib names.
    for elem_sel, attribs in loader_context.get("change_attribs", {}).items():
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            for attrib in elem.attrib.keys():
                if attrib in attribs:
                    old_attrib_value = elem.attrib.pop(attrib)
                    if attribs[attrib] is not None:
                        # If attribs[attrib] is None, attrib is removed instead of
                        # renamed.
                        elem.attrib[attribs[attrib]] = old_attrib_value
    return [tree]


def change_tags(tree, loader_context):
    # Change tag names.
    for elem_sel, elem_tag in loader_context.get("change_tags", {}).items():
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            elem.tag = elem_tag

    return [tree]


def cleanup_html(tree, loader_context):
    # tree.iter() iterates over the tree including the root node.
    for elem in tree.iter():
        # Remove class and id attribute from all elements which are not needed
        # in the feed.
        elem.attrib.pop("class", None)
        elem.attrib.pop("id", None)
        # Delete data- attributes that have no general meaning.
        for attrib in list(elem.attrib.keys()):
            if attrib.startswith("data-"):
                elem.attrib.pop(attrib)

    return [tree]


def lxml_cleaner(tree):
    cleaner = Cleaner(style=True)
    # Allow "srcset" and "sizes" attributes which are standardized for <img>.
    safe_attrs = set(cleaner.safe_attrs)
    safe_attrs.add("srcset")
    safe_attrs.add("sizes")
    cleaner.safe_attrs = frozenset(safe_attrs)
    cleaner(tree)
    return [tree]


def convert_footnotes(tree, loader_context):
    # Convert footnotes.
    for elem_sel in loader_context.get("convert_footnotes", []):
        selector = CSSSelector(elem_sel)
        for elem in selector(tree):
            if elem.text is not None:
                elem.tag = "small"
                elem.text = " ({})".format(elem.text.strip())

    return [tree]


def convert_iframes(tree, loader_context):
    """Convert iframes to divs with links to its src.

    convert_iframes() is called after remove_elems() so that unwanted iframes can be
    eliminated first.
    """
    base_url = loader_context.get("base_url", None) if loader_context else None
    selector = CSSSelector("iframe")
    for elem in selector(tree):
        if "src" not in elem.attrib:
            continue
        url = urljoin(base_url, elem.attrib.pop("src"))
        elem_new = lxml.html.fragment_fromstring(
            '<div><a href="{url}">{url}</a></div>'.format(url=url)
        )
        elem_new.tail = elem.tail
        elem.getparent().replace(elem, elem_new)

    return [tree]


def flatten_tree(tree):
    # Post-order traversal.
    for child in tree.iterchildren():
        flatten_tree(child)

    # Points to the first child if tree has a child and it's the only child or None
    # otherwise.
    only_child = list(tree)[0] if len(tree) == 1 else None
    if (
        tree.tag not in EMPTY_ELEMENTS
        and (tree.text is None or tree.text.strip() == "")
        and len(tree) == 0
        and tree.getparent() is not None
    ):
        # Remove elements which don't have a text and are not supposed to be empty.
        tree.drop_tree()
        return None
    elif (
        only_child is not None
        and (tree.text is None or tree.text.strip() == "")
        and only_child.tag == tree.tag
        and tree.getparent() is not None
    ):
        # Replace tree with child if there is only one child and it has the same tag.

        # Preserve both tails.
        new_tail = (only_child.tail or "") + (tree.tail or "")
        if not new_tail:
            new_tail = None
        only_child.tail = new_tail

        tree.getparent().replace(tree, only_child)

    return [tree]


def skip_empty_tree(tree):
    if tree.text:
        # Has a text.
        return [tree]

    if len(tree):
        # Has children.
        return [tree]

    return None


def skip_none(value):
    """Skip values that are None immediately."""
    if value is not None:
        return value

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


def truncate_tree(tree, limit, drop=False):
    """Truncates the tree in-place so that its text will not exceed limit characters.

    If the limit is exceeded, words are dropped and "..." is added to the end. The
    difference between the actual length of the text and the limit is returned.
    If drop is True, the tree itself will be removed from its parent.
    """

    def _truncate(text, width):
        shorten = len(text) > width
        if shorten:
            # shorten() removes trailing spaces, so we use TextWrapper directly.
            text = TextWrapper(
                width=width, max_lines=1, placeholder="...", drop_whitespace=False
            ).fill(text)
        return (text, width - len(text), shorten)

    remaining = limit

    if remaining < 10 or drop:
        # This will effectively remove all children and the tail as well.
        tree.getparent().remove(tree)
        truncated = True
    else:
        truncated = False

        # Try to truncate the text of the tree.
        if tree.text:
            tree.text, remaining, truncated = _truncate(tree.text, remaining)

        # If there was not enough text but there are children, try to truncate the
        # children.
        for child in tree:
            # drop children if truncation was already done.
            remaining, truncated = truncate_tree(child, remaining, drop=truncated)

        # If there is a tail either truncate it or remove it.
        if tree.tail:
            if remaining >= 10:
                tree.tail, remaining, truncated = _truncate(tree.tail, remaining)
            else:
                tree.tail = None

    return remaining, truncated


def truncate_text(text):
    settings = get_feeds_settings()
    truncate_words = settings.getint("FEEDS_CONFIG_TRUNCATE_WORDS")
    if truncate_words and truncate_words > 0:
        tree = build_tree(text)[0]
        # Assume that a word has 5 characters on average.
        truncate_tree(tree, truncate_words * 5)
        text = serialize_tree(tree)
    return text


class BaseItemLoader(ItemLoader):
    # Defaults
    # Unescape twice to get rid of &amp;&xxx; encoding errors.
    default_input_processor = MapCompose(
        skip_none, str.strip, skip_false, html.unescape, html.unescape
    )
    default_output_processor = TakeFirst()

    # Join first two elements on ": " and the rest on " - ".
    title_out = Compose(lambda t: [": ".join(t[:2])] + t[2:], Join(" - "))

    updated_in = MapCompose(skip_false, parse_datetime, apply_timezone)

    author_name_out = Join(", ")

    # Optional
    path_in = MapCompose(urlquote_plus)
    path_out = Identity()


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
        pullup_elems,
        replace_elems,
        remove_elems,
        change_attribs,
        change_tags,
        cleanup_html,
        convert_iframes,
        lxml_cleaner,
        flatten_tree,
        skip_empty_tree,
        make_links_absolute,
        make_srcset_absolute,
        serialize_tree,
    )
    content_html_out = Compose(Join(), truncate_text)

    # Use sorted to keep the output stable.
    category_out = Compose(set, sorted)

    enclosure_in = Identity()
    enclosure_out = Identity()
