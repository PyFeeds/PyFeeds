.. _spider_falter.at:

falter.at
---------
Get newest articles and restaurant reviews from Falter_.

Configuration
~~~~~~~~~~~~~
Add ``falter.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     falter.at

Falter_ has a paywall for certain articles. If you want to crawl paid
articles, please provide ``abonr`` (subscription number) and ``password``.

``pages`` accepts ``magazine`` for the Falter newspaper and
``lokalfuehrer_reviews``, ``lokalfuehrer_newest`` for restaurant, ``streams``
for movie streams and ``events`` for events. By default all are scraped.

``blogs`` accepts slugs for the blogs from https://cms.falter.at/blogs/.

``region`` accepts a region for events, e.g. ``wien`` (default).

.. code-block:: ini

   [falter.at]
   abonr =
   password =
   pages =
       magazine
       lokalfuehrer_reviews
       lokalfuehrer_newest
       streams
       events
   blogs =
       lingens
       thinktank

.. _Falter: https://www.falter.at
