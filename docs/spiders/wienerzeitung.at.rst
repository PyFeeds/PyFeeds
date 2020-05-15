.. _spider_wienerzeitung.at:

wienerzeitung.at
----------------
Newest articles from `Wiener Zeitung`_.

Configuration
~~~~~~~~~~~~~
Add ``wienerzeitung.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     wienerzeitung.at

wienerzeitung.at supports different ressorts via the ``ressorts`` parameter
(one per line).

Example configuration:

.. code-block:: ini

   [wienerzeitung.at]
   ressorts =
       nachrichten/politik/wien
       nachrichten/politik
       nachrichten/wirtschaft
       meinung

.. _`Wiener Zeitung`: https://www.wienerzeitung.at
