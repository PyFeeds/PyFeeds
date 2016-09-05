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
* `Libraries based on biblioweb <http://biblioweb.at>`_: Most recently added
  media to libraries based on the biblioweb software.
* `cbird.at <http://www.cbird.at>`_: Newest releases of the cbird software
* `falter.at <http://www.falter.at>`_: Newest articles
* `HELP.gv.at <https://help.gv.at>`_: News and changes in Austrian law
* `KONSUMENT.AT <http://www.konsument.at>`_: Newest articles
* `NZZ.at <http://www.nzz.at>`_: Newest articles
* `ORF Ö1 <http://oe1.orf.at>`_: Newest episodes of radio shows
* `ORF TVthek <http://tvthek.orf.at>`_: Newest episodes of TV shows
* `profil <http://www.profil.at>`_: Newest articles
* `puls 4 <http://www.puls4.com>`_: Newest episodes of TV shows (not including
   reairs)
* `Übermedien <http://www.uebermedien.de>`_: Newest articles
* `Wiener Linien <http://www.wienerlinien.at>`_: Newest articles

Some sites (Falter, Konsument, NZZ, Übermedien) offer articles only behind a
paywall. If you have a paid subscription, you can configure your username and
password in ``feeds.cfg`` and also read paywalled articles from within your
feed reader. For the less fortunate who don't have a subscription, paywalled
articles are tagged with ``paywalled`` so they can be filtered, if desired.

All feeds contain the articles in full text so you never have to leave your
feed reader while reading.

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

Related work
------------

* `morss <https://github.com/pictuga/morss>`_ creates feeds, similar to Feeds
  but in "real-time", i.e. on (HTTP) request.
* `Full-Text RSS <https://bitbucket.org/fivefilters/full-text-rss>`_ converts
  feeds to contain the full article and not only a teaser based on heuristics
  and rules. Feeds are converted in "real-time", i.e. on request basis.
* `f43.me <https://github.com/j0k3r/f43.me>`_ converts feeds to contain the
  full article and also improves articles by adding links to the comment
  sections of Hacker News and Reddit. Feeds are converted periodically.
* `python-ftr <https://github.com/1flow/python-ftr>`_ is a library to extract
  content from pages. A partial reimplementation of Full-Text RSS.

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

Author
------

Feeds is written and maintained by `Florian Preinstorfer
<https://www.nblock.org>`_ (`@nblock <https://twitter.com/krippala>`_) and
`Lukas Anzinger <https://www.notinventedhere.org>`_.

License
-------

AGPL3, see `LICENSE`_ for details.

.. _LICENSE: LICENSE
.. _issue tracker: https://github.com/nblock/feeds/issues
.. _new issue: https://github.com/nblock/feeds/issues/new
.. _Scrapy: http://www.scrapy.org
