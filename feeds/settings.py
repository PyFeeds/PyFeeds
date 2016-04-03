#!/usr/bin/python3

# Scrapy settings for feeds project

BOT_NAME = 'feeds'
SPIDER_MODULES = ['feeds.spiders']
NEWSPIDER_MODULE = 'feeds.spiders'
USER_AGENT = 'feeds (+https://feeds.nblock.org)'

# Disable telnet
TELNETCONSOLE_ENABLED = False

# Custom item pipeline
ITEM_PIPELINES = {
    'feeds.pipelines.AtomAutogenerateIdPipeline': 100,
    'feeds.pipelines.AtomCheckRequiredFieldsPipeline': 110,
    'feeds.pipelines.AtomCheckDictFieldsPipeline': 120,
    'feeds.pipelines.AtomExportPipeline': 400
}

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
