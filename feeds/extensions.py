
from scrapy import signals


class SpiderSettings:

    @classmethod
    def from_crawler(cls, crawler):
        ext = cls()
        crawler.signals.connect(ext.spider_opened,
                                signal=signals.spider_opened)
        return ext

    def spider_opened(self, spider):
        spider.spider_settings = self.spider_settings(spider)

    @classmethod
    def spider_settings(cls, spider):
        return spider.settings.get('FEEDS_CONFIG').get(spider.name, {})
