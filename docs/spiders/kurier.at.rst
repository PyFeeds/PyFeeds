.. _spider_kurier.at:

kurier.at
---------
Newest articles from Kurier.at_.

Configuration
~~~~~~~~~~~~~
Add ``kurier.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     kurier.at

kurier.at supports different channels via the ``channels`` parameter, articles
via the ``articles`` parameter and authors via the ``authors`` parameter (one
per line).

Example configuration:

.. code-block:: ini

    [kurier.at]
    channels =
        /chronik/wien
    articles =
        /meinung/pammesberger-2018-die-karikatur-zum-tag/309.629.015/slideshow
    authors =
        niki.glattauer
        guido.tartarotti
        florian.holzer
        barbara.kaufmann

.. _Kurier.at: https://kurier.at
