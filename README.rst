Feeds
=====

.. image:: https://travis-ci.org/nblock/feeds.svg?branch=master
    :target: https://travis-ci.org/nblock/feeds

Once upon a time every website offered an RSS feed to keep readers updated
about new articles/blog posts via the users' feed readers. These times are
long gone. The once iconic orange RSS icon has been replaced by "social share"
buttons.

Feeds aims to bring back the good old reading times. It creates Atom feeds for
websites that don't offer them (anymore). It allows you to read new articles
of your favorite websites in your feed reader (e.g. `Tiny Tiny RSS
<https://tt-rss.org>`_) even if this is not officially supported by the
website.

Feeds is based on Scrapy_, a framework for extracting data from websites, and
it's easy to add support for new websites. Just take a look at the existing
spiders in ``feeds/spiders`` and feel free to open a pull request!

Supported Websites
------------------

Feeds is currently able to create Atom feeds for the following sites:

* `ATV.at <http://www.atv.at>`_: Newest episodes of TV shows
* `Bibliothek der Arbeiterkammer <http://ak.ciando.com>`_: Most recently added
  books to the e-library
* `cbird.at <http://www.cbird.at>`_: Newest releases of the cbird software
* `falter.at <http://www.falter.at>`_: Newest articles
* `KONSUMENT.AT <http://www.konsument.at>`_: Newest articles
* `NZZ.at <http://www.nzz.at>`_: Newest articles
* `ORF Ö1 <http://oe1.orf.at>`_: Newest episodes of radio shows
* `ORF TVthek <http://tvthek.orf.at>`_: Newest episodes of TV shows
* `profil <http://www.profil.at>`_: Newest articles
* `Wiener Linien <http://www.wienerlinien.at>`_: Newest articles

Some sites (falter.at, NZZ.at, ...) offer articles only behind a paywall. If
you have a paid subscription, you can configure your username and password in
``feeds.cfg`` and also read paywalled articles from within your feed reader.
For the less fortunate paywalled articles are tagged ``paywalled`` so they can
be filtered if desired.

Installation
------------

Feeds is meant to be installed on your server and run periodically in a cron
job.

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
* Run ``feeds --help`` or ``feeds <subcommand> --help`` for help and usage
  details.

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
.. _Scrapy: http://www.scrapy.org
