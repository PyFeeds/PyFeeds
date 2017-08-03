.. _spider_vice.com:

vice.com
--------
Newest articles from VICE_.

Configuration
~~~~~~~~~~~~~
Add ``vice.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     vice.com

VICE_ supports different locations via the ``locales`` parameter (one per
line).

.. code-block:: ini

   [vice.com]
   locales =
     de_at
     de

.. _VICE: https://www.vice.com
