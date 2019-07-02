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

spotify.com supports different podcasts via the ``show`` parameter (one per
line).

Example configuration:

.. code-block:: ini

 [spotify.com]
 shows =
     6u7pI0o0CUBQq0T1fwPgbj
