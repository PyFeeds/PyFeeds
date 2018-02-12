.. _spider_nachrichten_at:

nachrichten.at
--------------
Newest articles from `Oberösterreichische Nachrichten`_.

Configuration
~~~~~~~~~~~~~
Add ``nachrichten.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     nachrichten.at

`Oberösterreichische Nachrichten`_ supports different ressorts via the
``ressorts`` parameter (one per line). If no ressort is given, the default
ressort "nachrichten" is used.

.. code-block:: ini

   [nachrichten.at]
   ressorts =
     linz
     wels

.. _Oberösterreichische Nachrichten: https://www.nachrichten.at
