.. _spider_arstechnica.com:

arstechnica.com
---------------
Full text feeds for `Ars Technica <https://arstechnica.com>`_.

Configuration
~~~~~~~~~~~~~
Add ``arstechnica.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     arstechnica.com

arstechnica.com supports different channels via the ``channels`` parameter
(one per line). If no channel is given, ``features`` is used. Go to
`RSS feeds <https://arstechnica.com/rss-feeds/>`_ for a list of all feeds.

.. code-block:: ini

   [arstechnica.com]
   channels =
     index
     features
     technology-lab
     gadgets
     business
     security
     tech-policy
     apple
     gaming
     science
     multiverse
     cars
     staff-blogs
     cardboard
     open-source
     microsoft
     software
     telecom
     web
