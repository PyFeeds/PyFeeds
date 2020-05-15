.. _spider_ft.com:

ft.com
------
Newest articles from ft.com_.

Configuration
~~~~~~~~~~~~~
Add ``ft.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     ft.com

ft.com supports different ressorts via the ``ressorts`` parameter (one per
line). The ressort is the path in the URL (e. g. for
https://www.ft.com/companies/technology the ressort is
``companies/technology``). For the homepage the special ressort ``homepage``
can be used.

Example configuration:

.. code-block:: ini

   [ft.com]
   ressorts =
       homepage
       the-big-read

.. _ft.com: https://www.ft.com
