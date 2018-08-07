.. _spider_lwn.net:

lwn.net
-------
Newest articles from LWN_ with special treatment of LWN_ Weekly Editions.
Please note that LWN_ requires the cache to be enabled to minimize useless
requests. In case you provide username and password, the session (cookie) is
also cached until the cache entry expires.

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
