import configparser
import logging
import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.python import failure
import click

logger = logging.getLogger(__name__)


def load_feeds_config(cmdline, file_=None):
    if file_:
        logger.debug('Parsing configuration file {} ...'.format(file_.name))
        # Parse configuration file and store result under FEEDS_CONFIG of
        # scrapy's settings API.
        parser = configparser.ConfigParser()
        parser.read_file(file_)
        config = {s: dict(parser.items(s)) for s in parser.sections()}
        import feeds.settings
        feeds.settings.FEEDS_CONFIG = config

    settings = get_project_settings()
    feeds_settings = settings.get('FEEDS_CONFIG').get('feeds', {})

    # Mapping of feeds config section to setting names.
    for settings_key, config_key in (
            settings.get('FEEDS_CFGFILE_MAPPING', {}).items()):
        settings.set(settings_key, feeds_settings.get(config_key))

    for settings_key, value_from_cmdline in (
            settings.get('FEEDS_CMDLINE_MAPPING', {}).items()):
        settings.set(settings_key, value_from_cmdline(cmdline))

    return settings


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
@click.option('--loglevel', '-l', default='info',
              type=click.Choice(['debug', 'info', 'warning', 'error']))
@click.option('--config', '-c', type=click.File(),
              help='Feeds configuration for feeds.')
@click.option('--pdb/--no-pdb', default=False, help='Enable pdb on failure.')
@click.pass_context
def cli(ctx, loglevel, config, pdb):
    """
    feeds creates feeds for pages that don't have feeds.
    """
    ctx.obj['loglevel'] = loglevel
    ctx.obj['config'] = config
    if pdb:
        failure.startDebugMode()
    os.chdir(os.path.dirname(os.path.realpath(__file__)))


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
    cmdline = {
        'loglevel': ctx.obj['loglevel'],
        'stats': stats,
    }
    settings = load_feeds_config(cmdline, ctx.obj['config'])
    process = CrawlerProcess(settings)

    spiders = spiders_to_crawl(process, spiders)
    if not spiders:
        logger.error('Please specify what spiders you want to run!')
    else:
        for spider in spiders:
            logger.info('Starting crawl of {} ...'.format(spider))
            process.crawl(spider)

    process.start()


@cli.command()
def list():
    """List all available spiders."""
    settings = get_project_settings()
    settings['LOG_ENABLED'] = False
    process = CrawlerProcess(settings)
    for s in sorted(process.spider_loader.list()):
        print(s)


def main():
    cli(obj={})
