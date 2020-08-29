.. _Supported Websites:

Supported Websites
==================
Feeds is currently able to create full text Atom feeds for the websites listed
below. All feeds contain the articles in full text so you never have to leave
your feed reader while reading.

A note on paywalls
------------------
Some sites (:ref:`Falter <spider_falter.at>`, :ref:`Konsument
<spider_konsument.at>`, :ref:`LWN <spider_lwn.net>`) offer articles only
behind a paywall. If you have a paid subscription, you can configure your
username and password in ``feeds.cfg`` (see also :ref:`Configure Feeds`) and
also paywalled articles will be included in full text in the created feed. If
you don't have a subscription and hence the full text cannot be included,
paywalled articles are tagged with ``paywalled`` so they can be filtered, if
desired.

Most popular sites
------------------

.. toctree::
   :maxdepth: 1

   spiders/arstechnica.com
   spiders/economist.com
   spiders/ft.com
   spiders/indiehackers.com
   spiders/lwn.net
   spiders/npr.org
   spiders/spotify.com
   spiders/vice.com

Support for generic sites
-------------------------

.. toctree::
   :maxdepth: 1

   spiders/generic

All supported sites
-------------------
.. toctree::
   :maxdepth: 1
   :glob:

   spiders/*
