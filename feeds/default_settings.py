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
HTTPCACHE_STORAGE = "feeds.extensions.FeedsCacheStorage"
HTTPCACHE_POLICY = "scrapy.extensions.httpcache.DummyPolicy"
HTTPCACHE_DIR = save_cache_path("feeds")
# We cache everything and delete cache entries (and every parent request) during
# cleanup.
HTTPCACHE_IGNORE_HTTP_CODES = []

# Default user agent. Can be overriden in feeds.cfg.
USER_AGENT = "feeds (+https://github.com/nblock/feeds)"

# Set default level to info.
# Can be overriden with --loglevel parameter.
LOG_LEVEL = logging.INFO

# Stats collection is disabled by default.
# Can be overriden with --stats parameter.
STATS_CLASS = "scrapy.statscollectors.DummyStatsCollector"
