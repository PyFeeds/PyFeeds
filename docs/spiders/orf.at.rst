.. _spider_orf.at:

orf.at
------
Newest articles from `ORF ON <http://www.orf.at>`_.

Configuration
~~~~~~~~~~~~~
Add ``orf.at`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     orf.at

orf.at supports different channels via the ``channels`` parameter (one per
line). If no channel is given, ``news`` is used. It also possible to give
a list of authors for which feeds will then be generated. Note that the
ressort in which the author writes still has to be included in the ressorts
parameter.

.. code-block:: ini

   [orf.at]
   ressorts =
     burgenland
     fm4
     help
     kaernten
     news
     noe
     oe3
     oesterreich
     ooe
     religion
     salzburg
     science
     sport
     steiermark
     tirol
     vorarlberg
     wien
   authors =
     Erich Moechel
