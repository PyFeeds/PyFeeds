.. _Configure Feeds:

Configure Feeds
===============
Feeds settings
--------------
Configuration settings related to Feeds need to be specified within the
``[feeds]`` section of the configuration file. The following settings are
supported.

useragent
~~~~~~~~~
The Useragent used for crawling.

.. code-block:: ini

   [feeds]
   useragent = feeds (+https://github.com/pyfeeds/pyfeeds)

spiders
~~~~~~~
Each spider listed in the ``spiders`` setting will be crawled with each run.
List one spider per line.

.. code-block:: ini

   [feeds]
   spiders =
     tvthek.orf.at
     oe1.orf.at

Use ``feeds list`` to get a list of all available spiders.

output_path
~~~~~~~~~~~
This is the path where the generated Atom feeds will be saved. You may serve
this directory with any webserver.

.. code-block:: ini

   [feeds]
   output_path = output

output_url
~~~~~~~~~~
The URL of the target directory from which the feeds can be accessed. This is
an optional setting and it is used to generate ``atom:link`` element with
``rel="self"`` attribute. See also:
https://validator.w3.org/feed/docs/warning/MissingSelf.html

.. code-block:: ini

   [feeds]
   output_url = https://example.com/feeds

truncate_words
~~~~~~~~~~~~~~
Truncate content to 10 words instead of including the full text. This can be
useful if generated feeds should be made publicly available.

.. code-block:: ini

   [feeds]
   truncate_words = 10

remove_images
~~~~~~~~~~~~~
Remove images from output. This can be useful if generated feeds should be made
publicly available.

.. code-block:: ini

   [feeds]
   remove_images = 1

cache_enabled
~~~~~~~~~~~~~
Feeds can be configured to use a cache for HTTP responses which is highly
recommended to save bandwidth. The ``cache_enabled`` setting controls whether
caching is used.

.. code-block:: ini

   [feeds]
   cache_enabled = 1

cache_dir
~~~~~~~~~
The path where cache data is stored.

.. code-block:: ini

   [feeds]
   cache_dir = ~/.cache/feeds

cache_expires
~~~~~~~~~~~~~
Expire (remove) entries from cache after 90 days.

.. code-block:: ini

   [feeds]
   cache_expires = 90

Spider specific settings
------------------------
Some spiders support additional settings. Head over to the :ref:`Supported
Websites` section for more information on spider specific settings.

.. _example configuration:

Example configuration
---------------------
Have a look at Feeds example configuration when configuring Feeds to suit your
needs.

.. literalinclude:: ../feeds.cfg.dist
