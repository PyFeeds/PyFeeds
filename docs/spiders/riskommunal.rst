.. _spider_riskommunal:

riskommunal
-----------
News from your local town or community, if their website is maintained with
`RIS Kommunal <https://info.riskommunal.net/>`_.

Configuration
~~~~~~~~~~~~~
Add ``riskommunal`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     riskommunal

At least one url is required. The local community or town website typically has
a "News" or "Neuigkeiten" URL that you may use.

.. code-block:: ini

   [riskommunal]
   urls =
       http://yourlocalcommunity.tld/News
       https://mytown.tld/BUeRGERSERVICE/Neuigkeiten
