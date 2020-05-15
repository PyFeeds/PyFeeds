.. _spider_economist.com:

economist.com
-------------
Newest articles from economist.com_.

Configuration
~~~~~~~~~~~~~
Add ``economist.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     economist.com

economist.com supports different ressorts via the ``ressorts`` parameter (one
per line). See https://www.economist.com/rss for a list of ressorts.

Example configuration:

.. code-block:: ini

   [economist.com]
   ressorts =
       finance-and-economics
       special-report
       leaders

.. _economist.com: https://www.economist.com
