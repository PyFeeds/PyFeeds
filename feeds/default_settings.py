import logging
import os

from xdg.BaseDirectory import save_cache_path, xdg_config_home

# Default settings for Feeds specific configurations.
FEEDS_CONFIG_OUTPUT_PATH = "output"
FEEDS_CONFIG_FILE = os.path.join(xdg_config_home, "feeds.cfg")
FEEDS_CONFIG_CACHE_EXPIRES = 90

# Low level settings intended for scrapy.
# Please use feeds.cfg to configure feeds.

BOT_NAME = "feeds"
SPIDER_MODULES = ["feeds.spiders"]
NEWSPIDER_MODULE = "feeds.spiders"

# Don't overwhelm sites with requests.
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 0.25

# Disable telnet
TELNETCONSOLE_ENABLED = False

# Custom item pipeline
ITEM_PIPELINES = {
    "feeds.pipelines.AtomAutogenerateFieldsPipeline": 100,
    "feeds.pipelines.AtomCheckRequiredFieldsPipeline": 110,
    "feeds.pipelines.AtomExportPipeline": 400,
}

SPIDER_MIDDLEWARES = {
    "feeds.spidermiddlewares.FeedsHttpErrorMiddleware": 51,
    "feeds.spidermiddlewares.FeedsHttpCacheMiddleware": 1000,
}

DOWNLOADER_MIDDLEWARES = {
    "feeds.downloadermiddlewares.FeedsHttpCacheMiddleware": 900,
    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": None,
}

HTTPCACHE_ENABLED = True
HTTPCACHE_STORAGE = "feeds.cache.FeedsCacheStorage"
HTTPCACHE_POLICY = "feeds.cache.FeedsCachePolicy"
HTTPCACHE_DIR = save_cache_path("feeds")
HTTPCACHE_EXPIRATION_SECS = FEEDS_CONFIG_CACHE_EXPIRES * 24 * 60 * 60
HTTPCACHE_IGNORE_HTTP_CODES = list(range(400, 600))

# Do not enable cookies by default to make better use of the cache.
COOKIES_ENABLED = False

RETRY_ENABLED = True
# equals 5 requests in total
RETRY_TIMES = 4

# Don't filter duplicates.
# Spiders sometimes produce feeds with potentially overlapping items.
DUPEFILTER_CLASS = "scrapy.dupefilters.BaseDupeFilter"

# Default user agent. Can be overriden in feeds.cfg.
USER_AGENT = "feeds (+https://github.com/pyfeeds/pyfeeds)"

# Set default level to info.
# Can be overriden with --loglevel parameter.
LOG_LEVEL = logging.INFO

# Stats collection is disabled by default.
# Can be overriden with --stats parameter.
STATS_CLASS = "scrapy.statscollectors.DummyStatsCollector"
