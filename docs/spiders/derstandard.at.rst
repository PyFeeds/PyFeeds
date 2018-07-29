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
(one per line). If no ressort is given, ``seite1`` is used.

Example configuration:

.. code-block:: ini

   [derstandard.at]
   ressorts =
       47
       4748
       etat
       immobilien


.. _derStandard.at: https://derstandard.at
