import logging
import os
from copy import deepcopy
from urllib.parse import urljoin

from lxml import etree
from scrapy.exporters import BaseItemExporter

from feeds.items import FeedEntryItem, FeedItem

logger = logging.getLogger(__name__)


class AtomExporter(BaseItemExporter):
    class AtomFeed(object):
        def __init__(self, exporter, link_self=None):
            self._exporter = exporter
            self._link_self = link_self
            self._feed_updated = None
            self._feed_items = []
            self._xml = etree.Element(
                "feed", nsmap={None: "http://www.w3.org/2005/Atom"}
            )
            self._ids = set()

        def add_item(self, item):
            if isinstance(item, FeedItem):
                if self._link_self:
                    item["link_self"] = self._link_self
                for child in self._convert_feed_item(item):
                    self._xml.insert(0, child)
            elif isinstance(item, FeedEntryItem):
                if item["id"] not in self._ids:
                    self._ids.add(item["id"])
                    entry = etree.Element("entry")
                    for child in self._convert_feed_item(item):
                        entry.append(child)
                    self._feed_items.append(entry)
                else:
                    logger.debug(
                        "Feed entry with id '{}' already in feed.".format(item["id"])
                    )

        def insert_updated(self):
            child = etree.Element("updated")
            child.text = self._feed_updated
            self._xml.insert(0, child)

        def sort(self, fields=("updated", "id"), default=0, reverse=True):
            for item in sorted(
                self._feed_items,
                reverse=reverse,
                key=lambda k: tuple(
                    k.findtext(field, default=default) for field in fields
                ),
            ):
                self._xml.append(item)

        def tostring(self, **kwargs):
            return etree.tostring(self._xml, **kwargs)

        def __len__(self):
            return len(self._feed_items)

        def _convert_feed_item(self, item):
            xml_items = []

            # Convert author related fields.
            author_item = self._convert_special_nested(
                item, "author", ("name", "email")
            )
            if author_item is not None:
                xml_items.append(author_item)

            # Convert link
            key = "link"
            if key in item:
                xml_items.append(self._convert_special_link(item, key, "alternate"))
                item.pop(key)

            # Convert link
            key = "link_self"
            if key in item:
                xml_items.append(self._convert_special_link(item, key, "self"))
                item.pop(key)

            # Convert content
            for key in ("content_text", "content_html"):
                if key in item:
                    xml_items.append(self._convert_special_content(item, key))
                    item.pop(key)

            # Convert enclosure
            key = "enclosure"
            if key in item:
                for enclosure in self._convert_special_enclosure(item, key):
                    xml_items.append(enclosure)
                item.pop(key)

            key = "category"
            if key in item:
                for category in self._convert_special_category(item, key):
                    xml_items.append(category)
                item.pop(key)

            # Convert remaining fields.
            for name, value in self._exporter._get_serialized_fields(
                item, default_value=""
            ):
                element = etree.Element(name)
                element.text = value
                xml_items.append(element)
                if name == "updated":
                    self._update_updated(value)

            return xml_items

        def _convert_special_nested(self, item, parent, children, sep="_"):
            children_items = []
            for full_key in [sep.join((parent, child)) for child in children]:
                if full_key in item:
                    children_items.append(
                        self._convert_special_single_element(item, full_key, sep)
                    )
                    item.pop(full_key)
            if children_items:
                element = etree.Element(parent)
                for children_item in children_items:
                    element.append(children_item)
                return element

        def _convert_special_single_element(self, item, key, sep):
            _, child_key = key.split(sep)
            element = etree.Element(child_key)
            element.text = item[key]
            return element

        def _convert_special_link(self, item, key, rel):
            xml_item = etree.Element("link")
            xml_item.set("rel", rel)
            xml_item.set("href", item[key])
            return xml_item

        def _convert_special_content(self, item, key):
            element_name, content_type = key.split("_")
            xml_item = etree.Element(element_name)
            xml_item.set("type", content_type)
            xml_item.text = item[key]
            return xml_item

        def _convert_special_enclosure(self, item, key):
            for enclosure in item[key]:
                xml_item = etree.Element("link")
                xml_item.set("rel", "enclosure")
                xml_item.set("href", enclosure["iri"])
                xml_item.set("type", enclosure["type"])
                yield xml_item

        def _convert_special_category(self, item, key):
            for category in item[key]:
                xml_item = etree.Element("category")
                xml_item.set("term", category)
                yield xml_item

        def _update_updated(self, raw_updated):
            if raw_updated is None:
                return

            if self._feed_updated is None or self._feed_updated < raw_updated:
                self._feed_updated = raw_updated

    def __init__(self, output_path, output_url, name, **kwargs):
        self._configure(kwargs)
        self._output_path = output_path
        self._output_url = output_url
        self._name = name
        self._feeds = {}
        self._pretty_print = kwargs.pop("pretty_print", True)

    def finish_exporting(self):
        for path, feed in self._feeds.items():
            path = os.path.join(self._output_path, path)
            if len(feed) == 0:
                logger.warning("Feed '{}' contains no items!".format(path))

            feed.insert_updated()
            feed.sort()
            feed = feed.tostring(
                encoding=self.encoding,
                pretty_print=self._pretty_print,
                xml_declaration=True,
            )
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                with open(path, "rb") as f:
                    logger.debug("Found existing feed at '{}'".format(path))
                    old_feed = f.read()
            except FileNotFoundError:
                old_feed = None
            if feed != old_feed:
                with open(path, "wb") as f:
                    f.write(feed)
            else:
                logger.debug(
                    "Feed content not changed, not overwriting feed '{}'".format(path)
                )

    def export_item(self, item):
        for path in item.pop("path", [""]):
            path = os.path.join(self._name, path, "feed.atom")
            if path not in self._feeds:
                if self._output_url:
                    link_self = urljoin(self._output_url, path)
                else:
                    link_self = None
                self._feeds[path] = self.AtomFeed(exporter=self, link_self=link_self)
            # add_item() is destructive, so add a copy.
            self._feeds[path].add_item(deepcopy(item))

        # Pop content fields since we don't want to have them in scrapy's debug
        # output.
        item.pop("content_html", None)
        item.pop("content_text", None)
