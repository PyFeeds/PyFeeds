.. _spider_derstandard.at:

derstandard.at
--------------
Newest articles from derStandard.at_.

Configuration
~~~~~~~~~~~~~
Add ``derstandard.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     derstandard.at

derstandard.at supports different ressorts via the ``ressorts`` parameter
(one per line).

The spider also has support user postings via the ``users`` parameter
(one per line).

Example configuration:

.. code-block:: ini

   [derstandard.at]
   ressorts =
       diskurs/kolumnen/rauscher
       etat
       immobilien
    users =
        4894
        571924


.. _derStandard.at: https://derstandard.at
