.. _spider_generic:

Generic full-text extraction
----------------------------
The generic spider can transform already existing Atom or RSS feeds, which
usually only contain a summary or a few lines of the content, into full
content feeds. It is similar to `Full-Text RSS`_ but uses a port of an older
version of Readability_ under the hood and currently doesn't support
site_config files. It works best for blog articles.

Some feeds already provide the full content but in a tag that is not used by
your feed reader. E.g. feeds created by Wordpress usually have the full
content in the "encoded" tag. In such cases it's best to add the URL to the
``fulltext_urls`` entry which extracts the content directly from the feed
without Readability_. There is a little helper script in
`scripts/check-for-fulltext-content`_ to detect if a feed contains full-text
content.

Configuration
~~~~~~~~~~~~~
Add ``generic`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     generic

Add the feed URLs (Atom or XML) to the config file.

.. code-block:: ini

   # List of URLs to RSS/Atom feeds to crawl, one per line.
   [generic]
   urls =
       https://www.example.com/feed.atom
       https://www.example.org/feed.xml
   fulltext_urls =
       https://myblog.example.com/feed/

.. _Readability: https://github.com/mozilla/readability
.. _`Full-Text RSS`: http://fivefilters.org/content-only/
.. _`scripts/check-for-fulltext-content`: https://github.com/PyFeeds/PyFeeds/blob/master/scripts/check-for-fulltext-content
