import logging
import os
import pickle
import shutil
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


IGNORE_HTTP_CODES = [403, 404] + list(range(500, 600))


def read_meta(root):
    with open(os.path.join(root, "pickled_meta"), "rb") as f:
        return pickle.load(f)


def cleanup_cache(cache_dir, expires):
    """Removes cache entries in path.

    Entries are removed if one of the conditions is true:
      - Response has a certain status code (e.g. 404).
      - Individual expiration date is reached (compared to now).
      - Timestamp of entry and expires exceeds now.
    """

    if expires < timedelta(0):
        raise ValueError("expires must be a positive timedelta.")

    logger.debug("Cleaning cache entries from {} ...".format(cache_dir))

    now = datetime.now(timezone.utc)
    for cache_entry_path, _dirs, files in os.walk(cache_dir, topdown=False):
        if "pickled_meta" in files:
            meta = read_meta(cache_entry_path)
            try:
                entry_expires = timedelta(seconds=meta["cache_expires"])
            except KeyError:
                entry_expires = expires
            entry_expires = min(entry_expires, expires)
            threshold = (
                datetime.fromtimestamp(meta["timestamp"], tz=timezone.utc)
                + entry_expires
            )
            if now > threshold:
                remove_cache_entry(cache_entry_path)
            elif meta["status"] in IGNORE_HTTP_CODES:
                remove_cache_entry(cache_entry_path, remove_parents=True)
        elif not os.path.samefile(cache_entry_path, cache_dir):
            # Try to delete parent directory of cache entries.
            try:
                os.rmdir(cache_entry_path)
            except OSError:
                # Not empty, don't care.
                pass

    logger.debug("Finished cleaning cache entries.")


def remove_cache_entry(cache_entry_path, remove_parents=False):
    if os.path.exists(cache_entry_path):
        meta = read_meta(cache_entry_path)
        if remove_parents:
            logger.debug(
                "Removing parent cache entries for URL {}".format(meta["response_url"])
            )
            spider_root = os.path.dirname(os.path.dirname(cache_entry_path))
            for fingerprint in meta["parents"]:
                path = os.path.join(spider_root, fingerprint[0:2], fingerprint)
                remove_cache_entry(path, read_meta(path)["response_url"])
        logger.debug("Removing cache entry for URL {}".format(meta["response_url"]))
        shutil.rmtree(cache_entry_path, ignore_errors=True)
    else:
        logger.debug("Cannot remove cache entry {}".format(cache_entry_path))
