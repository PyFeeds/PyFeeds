Feeds
=====

|pypi| |support| |licence|

|readthedocs|

|travis|

Once upon a time every website offered an RSS feed to keep readers updated
about new articles/blog posts via the users' feed readers. These times are
long gone. The once iconic orange RSS icon has been replaced by "social share"
buttons.

Feeds aims to bring back the good old reading times. It creates Atom feeds for
websites that don't offer them (anymore). It allows you to read new articles of
your favorite websites in your feed reader (e.g. TinyTinyRSS_) even if this is
not officially supported by the website.

Furthermore it can also enhance existing feeds by inlining the actual content
into the feed entry so it can be read without leaving the feed reader.

Feeds is based on Scrapy_, a framework for extracting data from websites, and
it's easy to add support for new websites. Just take a look at the existing
spiders_ and feel free to open a `pull request`_!

Documentation
-------------
Feeds comes with extensive documentation. It is available at
`https://pyfeeds.readthedocs.io <https://pyfeeds.readthedocs.io/en/latest/>`_.

Supported Websites
------------------

Feeds is currently able to create full text Atom feeds for various sites. The
complete list of `supported websites is available in the documentation
<https://pyfeeds.readthedocs.io/en/latest/spiders.html>`_.

Content behind paywalls
~~~~~~~~~~~~~~~~~~~~~~~

Some sites (Falter_, Konsument_, LWN_, `Oberösterreichische Nachrichten`_,
Übermedien_) offer articles only behind a paywall. If you have a paid
subscription, you can configure your username and password in ``feeds.cfg`` and
also read paywalled articles from within your feed reader. For the less
fortunate who don't have a subscription, paywalled articles are tagged with
``paywalled`` so they can be filtered, if desired.

All feeds contain the articles in full text so you never have to leave your
feed reader while reading.

Installation
------------

Feeds is meant to be installed on your server and run periodically in a cron
job or similar job scheduler. We recommend to install Feeds inside a virtual
environment.

Feeds can be installed from PyPI using ``pip``:

.. code-block:: bash

   $ pip install PyFeeds

You may also install the current development version. The master branch is
considered stable enough for daily use:

.. code-block:: bash

   $ pip install https://github.com/pyfeeds/pyfeeds/archive/master.tar.gz

After installation ``feeds`` is available in your virtual environment.

Feeds supports Python 3.6+.

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

Caching
-------

Feeds caches HTTP responses by default to save bandwidth. Entries are cached
for 90 days by default (this can be overwritten in the config file). Outdated
entries are purged from cache automatically after a crawl. It's also possible
to explicitly purge the cache from outdated entries::

  $ feeds --config feeds.cfg cleanup

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

Authors
-------
Feeds is written and maintained by `Florian Preinstorfer <https://nblock.org>`_
and `Lukas Anzinger <https://www.notinventedhere.org>`_.

License
-------

AGPL3, see https://pyfeeds.readthedocs.io/en/latest/license.html for details.

.. _issue tracker: https://github.com/pyfeeds/pyfeeds/issues
.. _new issue: https://github.com/pyfeeds/pyfeeds/issues/new
.. _Scrapy: https://www.scrapy.org
.. _TinyTinyRSS: https://tt-rss.org
.. _pull request: https://pyfeeds.readthedocs.io/en/latest/contribute.html
.. _spiders: https://github.com/PyFeeds/PyFeeds/tree/master/feeds/spiders
.. _Falter: https://pyfeeds.readthedocs.io/en/latest/spiders/falter.at.html
.. _Konsument: https://pyfeeds.readthedocs.io/en/latest/spiders/konsument.at.html
.. _LWN: https://pyfeeds.readthedocs.io/en/latest/spiders/lwn.net.html
.. _Oberösterreichische Nachrichten: https://pyfeeds.readthedocs.io/en/latest/spiders/nachrichten.at.html
.. _Übermedien: https://pyfeeds.readthedocs.io/en/latest/spiders/uebermedien.de.html

.. |pypi| image:: https://img.shields.io/pypi/v/pyfeeds.svg?style=flat-square
    :target: https://pypi.org/project/pyfeeds/
    :alt: pypi version

.. |support| image:: https://img.shields.io/pypi/pyversions/pyfeeds.svg?style=flat-square
    :target: https://pypi.org/project/pyfeeds/
    :alt: supported Python version

.. |licence| image:: https://img.shields.io/pypi/l/pyfeeds.svg?style=flat-square
    :target: https://pypi.org/project/pyfeeds/
    :alt: licence

.. |readthedocs| image:: https://img.shields.io/readthedocs/pyfeeds/latest.svg?style=flat-square&label=Read%20the%20Docs
   :alt: Read the documentation at https://pyfeeds.readthedocs.io/en/latest/
   :target: https://pyfeeds.readthedocs.io/en/latest/

.. |travis| image:: https://img.shields.io/travis/pyfeeds/pyfeeds/master.svg?style=flat-square&label=Travis%20Build
    :target: https://travis-ci.org/PyFeeds/PyFeeds
    :alt: travis build status
