import logging

# Feeds configuration populated by an optional feeds configuration file.
FEEDS_CONFIG = {}
FEEDS_CFGFILE_MAPPING = {
    'USER_AGENT': 'useragent',
    'LOG_LEVEL': 'loglevel',
    'HTTPCACHE_ENABLED': 'cache_enabled',
    'HTTPCACHE_DIR': 'cache_dir',
}
FEEDS_CMDLINE_MAPPING = {
    'LOG_LEVEL': lambda cmdline: cmdline['loglevel'].upper(),
    'STATS_CLASS': lambda cmdline: (
        'scrapy.statscollectors.MemoryStatsCollector' if cmdline['stats'] else
        'scrapy.statscollectors.DummyStatsCollector'
    ),
}

# Low level settings intended for scrapy.
# Please use feeds.cfg to configure feeds.

BOT_NAME = 'feeds'
SPIDER_MODULES = ['feeds.spiders']
NEWSPIDER_MODULE = 'feeds.spiders'

# Disable telnet
TELNETCONSOLE_ENABLED = False

# Custom item pipeline
ITEM_PIPELINES = {
    'feeds.pipelines.AtomAutogenerateIdPipeline': 100,
    'feeds.pipelines.AtomCheckRequiredFieldsPipeline': 110,
    'feeds.pipelines.AtomExportPipeline': 400
}

EXTENSIONS = {
    'feeds.extensions.SpiderSettings': 500,
}

SPIDER_MIDDLEWARES = {
    'feeds.middlewares.FeedsHttpErrorMiddleware': 51,
}

HTTPCACHE_ENABLED = False
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
HTTPCACHE_POLICY = 'scrapy.extensions.httpcache.DummyPolicy'
HTTPCACHE_DIR = 'cache'
HTTPCACHE_IGNORE_HTTP_CODES = [404, 500, 502, 503, 504]

# Default user agent. Can be overriden in feeds.cfg.
USER_AGENT = 'feeds (+https://github.com/nblock/feeds)'

# Set default level to info.
# Can be overriden with --loglevel parameter.
LOG_LEVEL = logging.INFO

# Stats collection is disabled by default.
# Can be overriden with --stats parameter.
STATS_CLASS = 'scrapy.statscollectors.DummyStatsCollector'

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
