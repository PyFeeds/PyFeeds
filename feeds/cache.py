import logging
import os
import pickle
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)


IGNORE_HTTP_CODES = [404, 500, 502, 503, 504]


def read_meta(root):
    with open(os.path.join(root, "pickled_meta"), "rb") as f:
        return pickle.load(f)


def cleanup_cache(cache_dir, max_age):
    """ Removes cache entries in path that are older than max_age. """

    logger.debug("Cleaning cache entries from {} ...".format(cache_dir))

    for cache_entry_path, _dirs, files in os.walk(cache_dir, topdown=False):
        if "pickled_meta" in files:
            meta = read_meta(cache_entry_path)

            timestamp = datetime.fromtimestamp(meta["timestamp"])
            if timestamp < max_age:
                remove_cache_entry(cache_entry_path, meta["response_url"])
            elif meta["status"] in IGNORE_HTTP_CODES:
                remove_cache_entry(cache_entry_path, meta["response_url"])
                logger.debug(
                    "Removing parent cache entries for URL {}".format(
                        meta["response_url"]
                    )
                )
                spider_root = os.path.dirname(os.path.dirname(cache_entry_path))
                # Remove parents as well.
                for fingerprint in meta["parents"]:
                    path = os.path.join(spider_root, fingerprint[0:2], fingerprint)
                    remove_cache_entry(path, read_meta(path)["response_url"])
        elif not os.path.samefile(cache_entry_path, cache_dir):
            # Try to delete parent directory of cache entries.
            try:
                os.rmdir(cache_entry_path)
            except OSError:
                # Not empty, don't care.
                pass

    logger.debug("Finished cleaning cache entries.")


def remove_cache_entry(cache_entry_path, url):
    logger.debug("Removing cache entry for URL {}".format(url))
    shutil.rmtree(cache_entry_path)
