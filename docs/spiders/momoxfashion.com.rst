.. _spider_momoxfashion.com:

momoxfashion.com
----------------
Items available for buying at `momoxfashion <https://www.momoxfashion.com>`_.

Configuration
~~~~~~~~~~~~~
Add ``momoxfashion.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     momoxfashion.com

By default, `newest items <https://www.momoxfashion.com/katalog?sortiertnach=neueste>`_
(from the first three pages) will be included. You can provide a list of links
in case you want to limit the items to a specific brand or size.

.. code-block:: ini

   [momoxfashion.com]
   links =
     /katalog?sortiertnach=neueste
