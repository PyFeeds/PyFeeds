import logging
from copy import copy

from scrapy import Request, signals
from scrapy.exceptions import NotConfigured
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.misc import load_object
from scrapy.utils.request import request_fingerprint

from feeds.exceptions import DropResponse

logger = logging.getLogger(__name__)


class FeedsHttpErrorMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def process_spider_exception(self, response, exception, spider):
        if isinstance(exception, HttpError):
            if response.status >= 500:
                # Transient errors usually caused by overloaded sites, updates, short
                # downtimes, etc.
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
    def __init__(self, settings):
        if not settings.getbool("HTTPCACHE_ENABLED"):
            raise NotConfigured
        self.storage = load_object(settings["HTTPCACHE_STORAGE"])(settings)

    @classmethod
    def from_crawler(cls, crawler):
        mw = cls(crawler.settings)

        # Note: this hook is a bit of a hack to intercept redirections
        crawler.signals.connect(mw.request_scheduled, signal=signals.request_scheduled)

        return mw

    def process_spider_output(self, response, result, spider):
        def _set_fingerprint(response, r):
            if isinstance(r, Request):
                # Chain fingerprints of response.request and new requests together.
                try:
                    r.meta["fingerprints"] = copy(response.request.meta["fingerprints"])
                except KeyError:
                    r.meta["fingerprints"] = []
            return r

        return (_set_fingerprint(response, r) for r in result or ())

    def request_scheduled(self, request, spider):
        try:
            request.meta["fingerprints"] = copy(request.meta["fingerprints"])
        except KeyError:
            request.meta["fingerprints"] = []
        logger.debug(
            "Parent fingerprints for request {}: {}".format(
                request, request.meta["fingerprints"]
            )
        )
        if not request.meta.get("dont_cache", False):
            fingerprint = request_fingerprint(request, include_headers=["Cookie"])
            request.meta["fingerprints"].append(fingerprint)
        else:
            logger.debug("Skipping fingerprinting uncached request {}".format(request))

    def process_spider_exception(self, response, exception, spider):
        # Note that due to Scrapy bug #220 this is *not* called if DropResponse is
        # raised from a generator.
        # See also https://github.com/scrapy/scrapy/issues/220.
        if isinstance(exception, DropResponse):
            if exception.transient:
                lgr = logger.info
            else:
                lgr = logger.warning
            lgr(exception)
            self.storage.remove_response(response, spider)
            return []
