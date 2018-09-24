.. _spider_ubup.com:

ubup.com
--------
Items available for buying at `ubup <https://www.ubup.com>`_.

Configuration
~~~~~~~~~~~~~
Add ``ubup.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     ubup.com

By default, `newest items <https://www.ubup.com/katalog?sortiertnach=neueste>`_
(from the first three pages) will be included. You can provide a list of links
in case you want to limit the items to a specific brand or size.

.. code-block:: ini

   [ubup.com]
   links =
     /katalog?sortiertnach=neueste
