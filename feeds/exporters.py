#!/usr/bin/python3

import os

from lxml import etree
from scrapy.exporters import BaseItemExporter

from feeds.items import FeedEntryItem
from feeds.items import FeedItem


class AtomExporter(BaseItemExporter):

    class AtomFeed(object):
        def __init__(self, header, exporter):
            self._exporter = exporter
            self._feed_updated = None
            self._feed_items = []
            self._xml = etree.Element('feed')
            self._xml.set('xmlns', 'http://www.w3.org/2005/Atom')
            for child in self._convert_feed_item(header):
                self._xml.insert(0, child)

        def export_item(self, item):
            entry = etree.Element('entry')
            for child in self._convert_feed_item(item):
                entry.append(child)
            self._feed_items.append(entry)

        def insert_updated(self):
            child = etree.Element('updated')
            child.text = self._feed_updated
            self._xml.insert(0, child)

        def sort(self, field='updated', default=0, reverse=True):
            for item in sorted(self._feed_items, reverse=reverse,
                               key=lambda k: k.findtext(field,
                                                        default=default)):
                self._xml.append(item)

        def tostring(self, **kwargs):
            return etree.tostring(self._xml, **kwargs)

        def _convert_feed_item(self, item):
            xml_items = []

            # Convert author related fields.
            author_item = self._convert_special_nested(
                item, 'author', ('name', 'email'))
            if author_item is not None:
                xml_items.append(author_item)

            # Convert link
            key = 'link'
            if key in item:
                xml_items.append(self._convert_special_link(item, key))
                item.pop(key)

            # Convert enclosure
            key_iri = 'enclosure_iri'
            key_type = 'enclosure_type'
            if key_iri in item:
                xml_items.append(self._convert_special_enclosure(item, key_iri,
                                 key_type))
                item.pop(key_iri)
                item.pop(key_type, None)

            # Convert content
            for key in ('content_text', 'content_html'):
                if key in item:
                    xml_items.append(self._convert_special_content(item, key))
                    item.pop(key)

            key = 'category'
            if key in item:
                for category in self._convert_special_category(item, key):
                    xml_items.append(category)
                item.pop(key)

            # Convert remaining fields.
            for name, value in self._exporter._get_serialized_fields(
                    item, default_value=''):
                element = etree.Element(name)
                element.text = value
                xml_items.append(element)
                if name == 'updated':
                    self._update_updated(value)

            return xml_items

        def _convert_special_nested(self, item, parent, children, sep='_'):
            children_items = []
            for full_key in [sep.join((parent, child)) for child in children]:
                if full_key in item:
                    children_items.append(
                        self._convert_special_single_element(item, full_key,
                                                             sep))
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

        def _convert_special_link(self, item, key):
            xml_item = etree.Element(key)
            xml_item.set('rel', 'alternate')
            xml_item.set('href', item[key])
            return xml_item

        def _convert_special_content(self, item, key):
            element_name, content_type = key.split('_')
            xml_item = etree.Element(element_name)
            xml_item.set('type', content_type)
            xml_item.text = item[key]
            return xml_item

        def _convert_special_enclosure(self, item, key_iri, key_type):
            xml_item = etree.Element('link')
            xml_item.set('rel', 'enclosure')
            xml_item.set('href', item[key_iri])
            xml_item.set('type', item[key_type])
            return xml_item

        def _convert_special_category(self, item, key):
            for category in item[key]:
                xml_item = etree.Element('category')
                xml_item.set('term', category)
                yield xml_item

        def _update_updated(self, raw_updated):
            if raw_updated is None:
                return

            if self._feed_updated is None or self._feed_updated < raw_updated:
                self._feed_updated = raw_updated

    def __init__(self, output_path, name, **kwargs):
        self._configure(kwargs)
        self._output_path = output_path
        self._name = name
        self._feeds = {}
        self._pretty_print = kwargs.pop('pretty_print', True)

    def finish_exporting(self):
        for path, feed in self._feeds.items():
            feed.insert_updated()
            feed.sort()
            path = os.path.join(self._output_path, path)
            os.makedirs(path, exist_ok=True)
            filename = os.path.join(path, 'feed.atom')
            with open(filename, 'wb') as f:
                f.write(feed.tostring(
                        encoding=self.encoding,
                        pretty_print=self._pretty_print,
                        xml_declaration=True))

    def export_item(self, item):
        try:
            path = os.path.join(self._name, item['path'])
        except KeyError:
            path = self._name
        if isinstance(item, FeedItem):
            self._feeds[path] = self.AtomFeed(header=item, exporter=self)
        elif isinstance(item, FeedEntryItem):
            self._feeds[path].export_item(item)

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
