.. _Docker:

Docker
==========

If you prefer to run Feeds in a docker container, you can use the official
`PyFeeds image <https://hub.docker.com/r/pyfeeds/pyfeeds/>`_.

A ``docker-compose.yaml`` could look like this:

.. code-block:: yaml

    version: "3.7"
    services:
      pyfeeds:
        image: pyfeeds/pyfeeds:latest
        volumes:
          - ./config:/config
          - pyfeeds-output:/output
        command: --config /config/feeds.cfg crawl
    volumes:
      pyfeeds-output:
        name: pyfeeds-output

It mounts the ``config`` folder next to the ``docker-compose.yaml`` and uses
the contained ``feeds.cfg`` as config for Feeds. The feeds are stored in a
volume which could be picked up by a webserver:

.. code-block:: yaml

    version: "3.7"
    services:
      pyfeeds-server:
        image: nginx:stable-alpine
        restart: always
        volumes:
          - pyfeeds-output:/usr/share/nginx/html:ro
    volumes:
      pyfeeds-output:
        external: true
        name: pyfeeds-output

Now any other container in the same docker network (f.e. a ttrss server) could
access the feeds (f.e. http://pyfeeds-server/theoatmeal.com/feed.atom).  Add a
port mapping in case you want to allow access from outside the container's
docker network.
