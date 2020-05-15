Get Feeds
=========
Feeds is meant to be installed on your server and run periodically in a cron
job or similar job scheduler.

The easiest way to install Feeds is via ``pip`` in a virtual environment. Feeds
does not provide any releases yet, so one might directly install the current
master branch:

.. code-block:: bash

    $ git clone https://github.com/pyfeeds/pyfeeds.git
    $ cd feeds
    $ python3 -m venv venv
    $ source bin/activate
    $ pip install -e .

After installation ``feeds`` is available in your virtual environment.

Feeds supports Python 3.6+.
