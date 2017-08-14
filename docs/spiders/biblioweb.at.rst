.. _spider_biblioweb.at:

biblioweb.at
------------
Most recently added media to libraries based on the biblioweb.at_ software.

Configuration
~~~~~~~~~~~~~
Add ``biblioweb.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     biblioweb.at

The ``location`` of your library that uses biblioweb.at_ is needed as
parameter.

.. code-block:: ini

   [biblioweb.at]
   location =

.. _biblioweb.at: https://www.biblioweb.at
