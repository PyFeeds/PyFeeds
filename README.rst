Feeds
=====

.. image:: https://travis-ci.org/nblock/feeds.svg?branch=master
    :target: https://travis-ci.org/nblock/feeds

DIY Atom feeds in times of social media and paywalls. Create Atom feeds from
websites that don't offer any.

Installation
------------

The easiest way to install Feeds is via ``pip`` in a virtual environment. Feeds
does not provide any releases yet, so one might directly install the current
master branch::

    $ git clone https://github.com/nblock/feeds.git
    $ cd feeds
    $ pip install .

After installation ``feeds`` is available in your virtual environment.

Feeds supports Python 3.3+.

Quickstart
----------

* List all available spiders::

  $ feeds list

* Feeds allows to crawl one or more spiders without configuration, e.g.::

  $ feeds crawl tvthek.orf.at

* A configuration file is supported too. Simply copy the template configuration
  and adjust it. Enable the spiders you are interested in and adjust the output
  path where Feeds stores the scraped Atom feeds::

  $ cp feeds.cfg.dist feeds.cfg
  $ $EDITOR feeds.cfg
  $ feeds --config feeds.cfg crawl

* Point your feed reader to the generated Atom feeds and start reading. Feeds
  works best when run periodically in a cron job.
* Run ``feeds --help`` or ``feeds <subcommand> --help`` to help and usage details.

How to contribute
-----------------

Issues
~~~~~~

* Search the existing issues in the `issue tracker`_.
* File a `new issue`_ in case the issue is undocumented.

Pull requests
~~~~~~~~~~~~~

* Fork the project to your private repository.
* Create a topic branch and make your desired changes.
* Open a pull request. Make sure the travis checks are passing.

License
-------

AGPL3, see `LICENSE`_ for details.

.. _LICENSE: LICENSE
.. _issue tracker: https://github.com/nblock/feeds/issues
.. _new issue: https://github.com/nblock/feeds/issues/new
