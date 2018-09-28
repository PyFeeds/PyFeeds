.. _spider_diepresse.com:

diepresse.com
-------------
Newest articles from DiePresse.com_.

Configuration
~~~~~~~~~~~~~
Add ``diepresse.com`` to the list of spiders:

.. code-block:: ini

   # List of spiders to run by default, one per line.
   spiders =
     diepresse.com

diepresse.com supports different sections (ressorts) via the ``sections``
parameter (one per line). If no section is given, ``all`` is used which is a
catch-all section that includes all articles. Sections must match exactly, not
only partially.

Example configuration:

.. code-block:: ini

   [diepresse.com]
   sections =
       Meinung/Pizzicato

.. _DiePresse.com: https://www.diepresse.com
