import logging
import os
import pickle
from datetime import datetime

logger = logging.getLogger(__name__)


def _read_meta(root):
    with open(os.path.join(root, "pickled_meta"), "rb") as f:
        return pickle.load(f)


def cleanup_cache(cache_dir, max_age):
    """ Removes cache entries in path that are older than max_age. """

    logger.debug("Cleaning cache entries from {} ...".format(cache_dir))

    for root, _dirs, files in os.walk(cache_dir, topdown=False):
        if "pickled_meta" in files:
            meta = _read_meta(root)
            timestamp = datetime.fromtimestamp(meta["timestamp"])
            if timestamp < max_age:
                logger.debug(
                    "Removing cache entry for URL {}".format(meta["response_url"])
                )
                for name in files:
                    os.remove(os.path.join(root, name))
                os.rmdir(root)
        elif not os.path.samefile(root, cache_dir):
            # Try to delete parent directory of cache entries.
            try:
                os.rmdir(root)
            except OSError:
                # Not empty, don't care.
                pass
