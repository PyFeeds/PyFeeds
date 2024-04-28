.. _spider_gem2go:

gem2go
------
News from your local town or community, if their website is maintained with
`GEM2GO <https://www.gem2go.at/>`_.

Configuration
~~~~~~~~~~~~~
Add ``gem2go`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     gem2go

At least one url is required. The local community or town website typically has
a "News" or "Neuigkeiten" URL that you may use.

.. code-block:: ini

   [gem2go]
   urls =
       http://yourlocalcommunity.tld/News
       https://mytown.tld/BUeRGERSERVICE/Neuigkeiten
