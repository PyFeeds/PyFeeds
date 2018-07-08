import logging

# Feeds configuration populated by an optional feeds configuration file.
FEEDS_CONFIG = {}

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

EXTENSIONS = {"feeds.extensions.SpiderSettings": 500}

SPIDER_MIDDLEWARES = {
    "feeds.spidermiddlewares.FeedsHttpErrorMiddleware": 51,
    "feeds.spidermiddlewares.FeedsHttpCacheMiddleware": 1000,
}

HTTPCACHE_ENABLED = False
HTTPCACHE_STORAGE = "feeds.extensions.FeedsCacheStorage"
HTTPCACHE_POLICY = "scrapy.extensions.httpcache.DummyPolicy"
HTTPCACHE_DIR = "cache"
# Cache regardless of the HTTP status by default, deal with purging unwanted status
# codes in feeds.cache.
HTTPCACHE_IGNORE_HTTP_CODES = []

# Default user agent. Can be overriden in feeds.cfg.
USER_AGENT = "feeds (+https://github.com/nblock/feeds)"

# Set default level to info.
# Can be overriden with --loglevel parameter.
LOG_LEVEL = logging.INFO

# Stats collection is disabled by default.
# Can be overriden with --stats parameter.
STATS_CLASS = "scrapy.statscollectors.DummyStatsCollector"

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
