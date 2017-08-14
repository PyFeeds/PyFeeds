.. _spider_facebook.com:

facebook.com
------------
Newest entries of selected pages from Facebook_.

Please note, that crawling user feeds is **not** supported.

Configuration
~~~~~~~~~~~~~
Add ``facebook.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     facebook.com

Facebook_ requires an ``app_id`` and ``app_secret`` for your app. These
credentials can be gathered by creating your own app at
`developers.facebook.com <https://developers.facebook.com>`_. In order to crawl
Facebook_ ``pages``, specify them as one page per line.

.. code-block:: ini

   [facebook.com]
   app_id =
   app_secret =
   # WARNING: Only pages can be crawled, NOT user profiles!
   pages =
     one_page_id
     per_line

.. _Facebook: https://facebook.com
