import uuid

from scrapy import signals
from scrapy.exceptions import DropItem

from feeds.exporters import AtomExporter
from feeds.items import FeedEntryItem


class AtomAutogenerateFieldsPipeline(object):
    """Autogenerate missing fields in case they are missing."""
    def process_item(self, item, spider):
        if 'id' not in item:
            if 'link' in item:
                item['id'] = uuid.uuid5(uuid.NAMESPACE_DNS, item['link']).urn
            else:
                raise DropItem('A link is required to autogenerate the feed '
                               'id for: {}'.format(item))

        if 'title' not in item:
            # Having a title is mandatory, so we use an empty string if none
            # is set.
            item['title'] = ''

        return item


class AtomCheckRequiredFieldsPipeline(object):
    """Check presence of required fields."""
    def process_item(self, item, spider):
        def raise_if_missing(name, item):
            if name not in item:
                raise DropItem('The required field "{}" is missing in: {}.'.
                               format(name, item))

        # Required fields for all items
        for required in ('id', 'title', 'link'):
            raise_if_missing(required, item)

        # Required fields for FeedEntryItems
        if isinstance(item, FeedEntryItem):
            for required in ('updated',):
                raise_if_missing(required, item)

        return item


class AtomExportPipeline(object):
    """Export items as atom feeds."""
    def __init__(self, output_path, output_url):
        self._output_path = output_path
        self._output_url = output_url
        self._exporters = {}

    @classmethod
    def from_crawler(cls, crawler):
        try:
            output_path = (
                crawler.settings.get('FEEDS_CONFIG')['feeds']['output_path']
            )
        except (KeyError, TypeError):
            output_path = 'output'
        try:
            output_url = (
                crawler.settings.get('FEEDS_CONFIG')['feeds']['output_url']
            )
        except (KeyError, TypeError):
            output_url = None
        pipeline = cls(output_path=output_path, output_url=output_url)
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self._exporters[spider] = AtomExporter(self._output_path,
                                               self._output_url, spider.name)
        self._exporters[spider].start_exporting()

    def spider_closed(self, spider):
        # Add feed header(s) at the end so they can be dynamic.
        for feed_header in spider.feed_headers():
            self._exporters[spider].export_item(feed_header)
        self._exporters[spider].finish_exporting()
        self._exporters.pop(spider)

    def process_item(self, item, spider):
        self._exporters[spider].export_item(item)
        return item

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
