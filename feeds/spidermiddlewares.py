from copy import copy
import logging

from scrapy import Request
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.request import request_fingerprint

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
                {"response": response},
                extra={"spider": spider},
            )
            return []


class FeedsHttpCacheMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_spider_output(self, response, result, spider):
        def _set_fingerprint(response, r):
            if isinstance(r, Request):
                try:
                    r.meta["fingerprints"] = copy(response.request.meta["fingerprints"])
                except KeyError:
                    r.meta["fingerprints"] = []
                if not response.request.meta.get("dont_cache", False):
                    fingerprint = request_fingerprint(response.request)
                    r.meta["fingerprints"].append(fingerprint)
                    logger.debug("Request fingerprints for request {}: {}".format(
                        r, r.meta["fingerprints"]))
                else:
                    logger.debug("Skipping fingerprinting uncached request {}".format(
                        response.request))
            return r
        return (_set_fingerprint(response, r) for r in result or ())
