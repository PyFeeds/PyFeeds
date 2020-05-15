import logging
import os

import click
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
from twisted.python import failure

from feeds.cache import FeedsCache
from feeds.settings import load_feeds_settings

logger = logging.getLogger(__name__)


def run_cleanup_cache(settings):
    cache = FeedsCache(settings)
    cache.cleanup()


def spiders_to_crawl(process, argument_spiders):
    if argument_spiders:
        # Spider(s) given as command line argument(s).
        logger.debug("Using command line to decide what spiders to run.")
        return argument_spiders

    try:
        # Spider(s) given in configuration file.
        spiders = process.settings.get("FEEDS_CONFIG_SPIDERS")
        logger.debug("Using configuration file to decide what spiders to run.")
        if spiders:
            return spiders.split()
        return None
    except KeyError:
        # Load all available spiders.
        logger.debug("All available spiders will be run.")
        return process.spider_loader.list()


@click.group()
@click.option(
    "--loglevel",
    "-l",
    default="info",
    type=click.Choice(["debug", "info", "warning", "error"]),
)
@click.option(
    "--config", "-c", type=click.File(), help="Feeds configuration for feeds."
)
@click.option("--pdb/--no-pdb", default=False, help="Enable pdb on failure.")
@click.pass_context
def cli(ctx, loglevel, config, pdb):
    """
    feeds creates feeds for pages that don't have feeds.
    """
    if pdb:
        failure.startDebugMode()

    # A pip-installed Feeds does not have a scrapy.cfg in its project root.
    os.environ["SCRAPY_SETTINGS_MODULE"] = "feeds.default_settings"

    settings = load_feeds_settings(config)
    settings.set("LOG_LEVEL", loglevel.upper())
    ctx.obj["settings"] = settings


@cli.command()
@click.argument("spiders", nargs=-1)
@click.option("--stats/--no-stats", default=False, help="Output scraping stats.")
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
    settings = ctx.obj["settings"]
    if stats:
        settings.set("STATS_CLASS", "scrapy.statscollectors.MemoryStatsCollector")

    # Start a new crawler process.
    process = CrawlerProcess(settings)
    spiders = spiders_to_crawl(process, spiders)
    if not spiders:
        logger.error("Please specify what spiders you want to run!")
    else:
        for spider in spiders:
            logger.info("Starting crawl of {} ...".format(spider))
            process.crawl(spider)

    process.start()

    if settings.getbool("HTTPCACHE_ENABLED"):
        run_cleanup_cache(settings)


@cli.command()
def list():
    """List all available spiders."""
    settings = get_project_settings()
    settings["LOG_ENABLED"] = False
    process = CrawlerProcess(settings)
    for s in sorted(process.spider_loader.list()):
        print(s)


@cli.command()
@click.pass_context
def cleanup(ctx):
    """
    Cleanup old cache entries.

    By default, entries older than 90 days will be removed. This value can be
    overriden in the config file.
    """
    settings = ctx.obj["settings"]
    # Manually configure logging since we don't have a CrawlerProcess which
    # would take care of that.
    configure_logging(settings)

    if not settings.getbool("HTTPCACHE_ENABLED"):
        logger.error("Cache is disabled, will not clean up cache dir.")
        return 1

    run_cleanup_cache(settings)


def main():
    cli(obj={})
