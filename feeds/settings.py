#!/usr/bin/python3

import logging

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

# Default user agent. Can be overriden in feeds.cfg.
USER_AGENT = 'feeds (+https://github.com/nblock/feeds)'

# Set default level to info. Can be overriden with --loglevel parameter.
LOG_LEVEL = logging.INFO

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
