import logging

from scrapy.spidermiddlewares.httperror import HttpError

logger = logging.getLogger(__name__)


class FeedsHttpErrorMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_spider_exception(self, response, exception, spider):
        if isinstance(exception, HttpError):
            logger.warning(
                "Ignoring response %(response)r: HTTP status code is not "
                "handled or not allowed",
                {'response': response}, extra={'spider': spider},
            )
            return []
