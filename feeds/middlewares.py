import logging

from scrapy.spidermiddlewares.httperror import HttpError

logger = logging.getLogger(__name__)


class FeedsHttpErrorMiddleware:

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_spider_exception(self, response, exception, spider):
        if isinstance(exception, HttpError):
            if response.status in [500, 502, 503, 504]:
                # These status codes are usually induced by overloaded sites,
                # updates, short downtimes, etc. and are not that relevant.
                lgr = logger.info
            else:
                lgr = logger.warning
            lgr(
                "Ignoring response %(response)r: HTTP status code is not "
                "handled or not allowed",
                {'response': response}, extra={'spider': spider},
            )
            return []
