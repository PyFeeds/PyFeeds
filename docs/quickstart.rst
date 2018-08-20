Quickstart
==========
Feeds has a few commands that are described on this page.

* List all available spiders:

  .. code-block:: bash

     $ feeds list

* Feeds allows to crawl one or more spiders without a configuration file, e.g.:

  .. code-block:: bash

     $ feeds crawl indiehackers.com

* A :ref:`configuration file <Configure Feeds>` is supported too. Simply copy
  the :ref:`example configuration` and adjust it. Enable the spiders you are
  interested in and adjust the ``output_path`` where Feeds stores the scraped
  Atom feeds:

  .. code-block:: bash

     $ cp feeds.cfg.dist feeds.cfg
     $ $EDITOR feeds.cfg
     $ feeds --config feeds.cfg crawl

* Perform a cache cleanup:

  .. code-block:: bash

     $ feeds --config feeds.cfg cleanup

* Point your feed reader to the generated Atom feeds and start reading. Feeds
  works best when run periodically in a cron job or similar job scheduler.

* Run ``feeds --help`` or ``feeds <subcommand> --help`` for help and usage
  details.
