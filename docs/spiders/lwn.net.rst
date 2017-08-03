.. _spider_lwn.net:

lwn.net
-------
Newest articles from LWN_ with special treatment of LWN_ Weekly Editions.

Configuration
~~~~~~~~~~~~~
Add ``lwn.net`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     lwn.net

LWN_ has paywalled articles. If you want to crawl them, please provide
``username`` and ``password``.

.. code-block:: ini

   [lwn.net]
   username =
   password =

.. _LWN: https://lwn.net
