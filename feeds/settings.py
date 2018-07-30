import configparser
import logging

from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)

_SETTINGS = None


def load_feeds_settings(file_):
    settings = get_project_settings()
    set_feeds_settings(settings)
    if not file_:
        config_file_path = settings.get("FEEDS_CONFIG_FILE")
        try:
            file_ = open(config_file_path, "r")
        except IOError:
            logger.info("Could not load config file from {}!".format(config_file_path))
            return settings

    logger.debug("Parsing configuration file {} ...".format(file_.name))
    # Parse configuration file and store result under FEEDS_CONFIG of scrapy's
    # settings API.
    config = configparser.ConfigParser()
    config.read_file(file_)
    feeds_config = {s: dict(config.items(s)) for s in config.sections()}

    for key, value in feeds_config["feeds"].items():
        settings.set("FEEDS_CONFIG_{}".format(key.upper()), value)

    del feeds_config["feeds"]

    for spider in feeds_config.keys():
        spider_key = spider.replace(".", "_").upper()
        for key, value in feeds_config[spider].items():
            settings.set("FEEDS_SPIDER_{}_{}".format(spider_key, key.upper()), value)

    # Mapping of feeds config section to setting names.
    feeds_cfgfile_mapping = {
        "USER_AGENT": config.get("feeds", "useragent", fallback=None),
        "LOG_LEVEL": config.get("feeds", "loglevel", fallback=None),
        "HTTPCACHE_ENABLED": config.getboolean("feeds", "cache_enabled", fallback=None),
        "HTTPCACHE_DIR": config.get("feeds", "cache_dir", fallback=None),
    }
    for key, value in feeds_cfgfile_mapping.items():
        if value is not None:
            settings.set(key, value)

    file_.close()

    return settings


def get_feeds_settings():
    return _SETTINGS


def set_feeds_settings(settings):
    global _SETTINGS
    _SETTINGS = settings
