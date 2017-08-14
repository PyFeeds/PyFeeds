.. _Supported Websites:

Supported Websites
==================
Feeds is currently able to create Atom feeds for the following websites:

.. toctree::
   :maxdepth: 1
   :glob:

   spiders/*

Some sites (:ref:`Falter <spider_falter.at>`, :ref:`Konsument
<spider_konsument.at>`, :ref:`LWN <spider_lwn.net>`, :ref:`Übermedien
<spider_uebermedien.com>`) offer articles only behind a paywall. If you have a
paid subscription, you can configure your username and password in
``feeds.cfg`` and also read paywalled articles from within your feed reader.
For the less fortunate who don't have a subscription, paywalled articles are
tagged with ``paywalled`` so they can be filtered, if desired.

All feeds contain the articles in full text so you never have to leave your
feed reader while reading.
