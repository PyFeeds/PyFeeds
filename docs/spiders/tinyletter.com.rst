.. _spider_tinyletter.com:

tinyletter.com
--------------
Latest articles from `tinyletter <tinyletter.com>`_ users.

Configuration
~~~~~~~~~~~~~
Add ``tinyletter.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     tinyletter.com

At least one account is required. The account name is visible on the
subscription page, e.g. for http://tinyletter.com/dabeaz, the account name is
``dabeaz``.

.. code-block:: ini

   [tinyletter.com]
   accounts =
     dabeaz
