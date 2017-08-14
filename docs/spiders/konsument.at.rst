.. _spider_konsument.at:

konsument.at
------------
Get newest articles from `konsument.at <https://www.konsument.at>`_.

Configuration
~~~~~~~~~~~~~
Add ``konsument.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     konsument.at

This website has a paywall for certain articles. If you want to crawl paid
articles, please provide ``username`` and ``password``:

.. code-block:: ini

   [konsument.at]
   username =
   password =
