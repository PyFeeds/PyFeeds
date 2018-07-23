.. _spider_falter.at:

falter.at
---------
Get newest articles and restaurant reviews ("wwei") from Falter_.

Configuration
~~~~~~~~~~~~~
Add ``falter.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     falter.at

Falter_ has a paywall for certain articles. If you want to crawl paid articles, please
provide ``abonr`` (subscription number) and ``password``.

``pages`` accepts ``magazine`` for the Falter newspaper and ``wwei`` for the restaurant
reviews. By default both are scraped.

.. code-block:: ini

   [falter.at]
   abonr =
   password =
   pages =
       magazine
       wwei

.. _Falter: https://www.falter.at
