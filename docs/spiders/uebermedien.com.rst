.. _spider_uebermedien.com:

uebermedien.com
---------------
Newest articles from Übermedien_.

Configuration
~~~~~~~~~~~~~
Add ``uebermedien.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     uebermedien.com


Übermedien_ has a paywall for certain articles. If you want to crawl paid
articles, please provide your Blendle ``username`` and ``password``.

.. code-block:: ini

   [uebermedien.de]
   username =
   password =

.. _Übermedien: http://www.uebermedien.de
