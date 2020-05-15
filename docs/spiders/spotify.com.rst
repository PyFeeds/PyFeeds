.. _spider_spotify.com:

spotify.com
-----------
Podcasts hosted on Spotify.

Configuration
~~~~~~~~~~~~~
Add ``spotify.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     spotify.com

The market you are in (i. e. your country as an ISO 3166-1 alpha-2 country
code) has to be specified in the config as well. For example, for Austria
specify: ``market = AT``

spotify.com supports different podcasts via the ``show`` parameter (one per
line).

Example configuration:

.. code-block:: ini

 [spotify.com]
 market = AT
 shows =
     6u7pI0o0CUBQq0T1fwPgbj
