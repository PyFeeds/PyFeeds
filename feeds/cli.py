import configparser
import logging

import click
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)


def load_feeds_config(settings, loglevel, stats, f):
    settings.set('LOG_LEVEL', loglevel.upper())

    if not stats:
        settings.set('STATS_CLASS',
                     'scrapy.statscollectors.DummyStatsCollector')

    if not f:
        # No configuration file given.
        settings.set('FEEDS_CONFIG', {})
        return

    logger.debug('Parsing configuration file {} ...'.format(f.name))
    # Parse configuration file and store result under FEEDS_CONFIG of scrapy's
    # settings API.
    parser = configparser.ConfigParser()
    parser.read_file(f)
    config = {s: dict(parser.items(s)) for s in parser.sections()}
    settings.set('FEEDS_CONFIG', config)

    try:
        useragent = config['feeds']['useragent']
        settings.set('USER_AGENT', useragent)
        logger.debug('Setting user agent to "{}"'.format(useragent))
    except KeyError:
        pass


def spiders_to_crawl(process, argument_spiders):
    if argument_spiders:
        # Spider(s) given as command line argument(s).
        logger.debug('Using command line to decide what spiders to run.')
        return argument_spiders

    try:
        # Spider(s) given in configuration file.
        spiders = process.settings.get('FEEDS_CONFIG')['feeds']['spiders']
        logger.debug('Using configuration file to decide what spiders to run.')
        return spiders.split()
    except KeyError:
        # Load all available spiders.
        logger.debug('All available spiders will be run.')
        return process.spider_loader.list()


@click.group()
@click.option('--loglevel', default='info',
              type=click.Choice(['debug', 'info', 'warning', 'error']))
@click.option('--config', '-c', type=click.File(),
              help='Feeds configuration for feeds.')
@click.pass_context
def cli(ctx, loglevel, config):
    """
    feeds creates feeds for pages that don't have feeds.
    """
    ctx.obj['loglevel'] = loglevel
    ctx.obj['config'] = config


@cli.command()
@click.argument('spiders', nargs=-1)
@click.option('--stats/--no-stats', default=False,
              help='Output scraping stats.')
@click.pass_context
def crawl(ctx, spiders, stats):
    """
    Crawl one or many or all pages.

    What spider(s) to run is determined in the following order:

      1. Spider(s) given as argument(s)

      2. Spider(s) specified in the configuration file

    Note that if a spider is given as an argument, the spiders in the
    configuration file are ignored. All available spiders will be used to
    crawl if no arguments are given and no spiders are configured.
    """
    # Start a new crawler process.
    settings = get_project_settings()
    load_feeds_config(settings, ctx.obj['loglevel'], stats, ctx.obj['config'])
    process = CrawlerProcess(settings)

    spiders = spiders_to_crawl(process, spiders)
    if not spiders:
        logger.error('Please specifiy what spiders you want to run!')
    else:
        for spider in spiders:
            logger.info('Starting crawl of {} ...'.format(spider))
            process.crawl(spider)

    process.start()


def main():
    cli(obj={})
