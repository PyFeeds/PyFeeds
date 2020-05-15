.. _spider_flimmit.com:

flimmit.com
-----------
Newly added movies, TV shows at `flimmit.com <https://www.flimmit.com>`_.

Configuration
~~~~~~~~~~~~~
Add ``flimmit.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     flimmit.com

By default, all categories (Filme, Serien, Europa, Kinder) will be included.
You can provide a list of categories.

.. code-block:: ini

   [flimmit.com]
   categories =
     filme
     serien
