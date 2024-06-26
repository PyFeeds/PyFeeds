.. _Development:

Supporting a new Website
========================
Feeds already supports a number of websites (see :ref:`Supported Websites`) but
adding support for a new website doesn't take too much time. All you need to do
is write a so-called spider. A spider is a Python class that is used by Feeds
to extract content from a website.

The feed generation pipeline looks like this:

  #. A spider extracts the content (e.g. an article) that should be part of
     the feed from a website. The spider also tells Feeds how the content
     should be cleaned up, e.g. which HTML elements should be removed.
  #. Feeds takes the content, cleans it up with the hints from the spider and
     some generic cleanup rules (e.g. ``<script>`` tags are always removed).
  #. Feeds writes an Atom feed for that site with the cleaned content to the
     file system.

A quick example
---------------
Writing a spider is easy! For simple websites it can be done in only about 30
lines of code.

Consider this example for a fictional website that hosts articles. When a new
article is published, a link to it is added to an overview page.  The idea is
now to use that URL as a starting point for the spider and let the spider
extract all the URLs to the articles. In the next step, the spider visits
every article, extracts the article text and meta information (time, author)
and creates a feed item out of it.

The following code shows how such a spider could look like for our example
website:

.. code-block:: python

    import scrapy

    from feeds.loaders import FeedEntryItemLoader
    from feeds.spiders import FeedsSpider


    class ExampleComSpider(FeedsSpider):
        name = "example.com"
        start_urls = ["https://www.example.com/articles"]
        feed_title = "Example Website"

        def parse(self, response):
            article_links = response.css(".article__link::attr(href)").extract()
            for link in article_links:
                yield scrapy.Request(response.urljoin(link), self._parse_article)

        def _parse_article(self, response):
            remove_elems = [".shareable-quote", ".share-bar"]
            il = FeedEntryItemLoader(
                response=response,
                base_url="https://{}".format(self.name),
                remove_elems=remove_elems,
            )
            il.add_value("link", response.url)
            il.add_css("title", "h1::text")
            il.add_css("author_name", "header .user-link__name::text")
            il.add_css("content_html", ".article-body")
            il.add_css("updated", ".article-date::text")
            return il.load_item()


First, the URL from the ``start_urls`` list is downloaded and the response is
given to ``parse()``. From there we extract the article links that should be
scraped and yield ``scrapy.Request`` objects from the for loop. The callback
method ``_parse_article()`` is executed once the download has finished. It
extracts the article from the response HTML document and returns an item that
will be placed into the feed automatically.

It's enough to place the spider in the ``spiders`` folder. It doesn't have to
be registered somewhere for Feeds to pick it up. Now you can run it::

    $ feeds crawl example.com

The resulting feed can be found in ``output/example.com/feed.xml``.

Reusing an existing feed
------------------------
Often websites provide a feed but it's not full text.  In such cases you
usually only want to augment the original feed with the full article.

Generic spider
~~~~~~~~~~~~~~
For a lot of feeds (especially those from blogs) it is actually sufficient to
use the :ref:`spider_generic` spider which can extract content from any website
using heuristics (go to :ref:`spider_generic` for more on that).

Note that a lot of feeds (e.g. those generated by Wordpress) actually contain
the full text but your feed reader chooses to show a summary instead. In such
cases you can also use the :ref:`spider_generic` spider and add your feed URL
to the ``fulltext_urls`` key in the config. This will create a full text feed
from an existing feed without having to rely on heuristics.

Custom extraction
~~~~~~~~~~~~~~~~~
These spiders take an existing RSS feed and inline the article content while
cleaning up the content (removing share buttons, etc.):

  * :ref:`spider_arstechnica.com`
  * :ref:`spider_derstandard.at`
  * :ref:`spider_ft.com`
  * :ref:`spider_lwn.net`
  * :ref:`spider_orf.at`
  * :ref:`spider_profil.at`

Paywalled content
~~~~~~~~~~~~~~~~~
If your website has a feed but some or all articles are behind a paywall or
require to login to read, take a look at the following spiders:

  * :ref:`spider_lwn.net`
  * :ref:`spider_nachrichten_at`
  * :ref:`spider_uebermedien.de`

Creating a feed from scratch
----------------------------
Some websites don't offer any feed at all. In such cases we have to find an
efficient way to detect new content and extract it.

Utilizing an API
~~~~~~~~~~~~~~~~
Some use a REST API which we can use to fetch the content.

  * :ref:`spider_falter.at`
  * :ref:`spider_indiehackers.com`
  * :ref:`spider_kurier.at`
  * :ref:`spider_oe1.orf.at`
  * :ref:`spider_tvthek.orf.at`
  * :ref:`spider_vice.com`

Utilizing the sitemap
~~~~~~~~~~~~~~~~~~~~~
Others provide a sitemap_ which we can parse:

  * :ref:`spider_trend.at`

Custom extraction
~~~~~~~~~~~~~~~~~
The last resort is to find a page that lists the newest articles and start
scraping from there.

  * :ref:`spider_atv.at`
  * :ref:`spider_biblioweb.at`
  * :ref:`spider_cbird.at`
  * :ref:`spider_economist.com`
  * :ref:`spider_lbg.at`
  * :ref:`spider_npr.org`
  * :ref:`spider_puls4.com`
  * :ref:`spider_python-patterns.guide`
  * :ref:`spider_gem2go`
  * :ref:`spider_servustv.com`
  * :ref:`spider_tuwien.ac.at`
  * :ref:`spider_momoxfashion.com`
  * :ref:`spider_usenix.org`
  * :ref:`spider_verbraucherrecht.at`
  * :ref:`spider_wienerlinien.at`
  * :ref:`spider_zeit.diebin.at`

For paywalled content, take a look at:

  * :ref:`spider_falter.at`
  * :ref:`spider_konsument.at`

Extraction rules
----------------
A great feed transports all the information from the original site but without
the clutter. The reader should never have to leave their reader and go to the
original site. The following rules help to reach that goal.

Unwanted content
~~~~~~~~~~~~~~~~
Advertisement, share buttons/links, navigation elements and everything
that is not part of the content is removed. The output should be similar to
what Firefox Reader View (Readability) outputs, but more polished.

Images
~~~~~~
The HTML tags ``<figure>`` and ``<figcaption>`` are used for figures (if
possible).
Example:

.. code-block:: html

   <figure>
   <div><img src="https://example.com/img.jpg"></img><div>
   <figcaption>A very interesting image.</figcaption>
   </figure>

Credits for images are removed. Images are included in their highest resolution
available.

Depaginate
~~~~~~~~~~
If content is split in multiple pages, all pages are scraped.

Iframes
~~~~~~~
Iframes are removed if they are unnecessary or untouched. Iframes are
automatically replaced with a link to their source.

Updated field
~~~~~~~~~~~~~
Every feed item has an updated field. If the spider cannot provide such a field
for an item because the original site doesn't expose that information, Feeds
will automatically use the timestamp when it saw the link of the item for the
first time.

Not embeddable content
~~~~~~~~~~~~~~~~~~~~~~
Sometimes external content like videos cannot be included in the feed because
it needs JavaScript. In such cases the container of the external video is
replaced with a note that says that the content is only available in the
original content.

Regular expressions
~~~~~~~~~~~~~~~~~~~
Regular expressions are only used to replace content if using CSS selectors
with ``replace_elems`` is not possible.

Categories
~~~~~~~~~~
A feed item has categories taken from its original feed or from the site.

Headings
~~~~~~~~
``<h*>`` tags are used for headings (i. e. not generic tags like ``<p>`` or
``<div>``). Headings start with ``<h2>``. The title of the content is not part
of the content and is removed.

Author name(s)
~~~~~~~~~~~~~~
The name of all authors are added to the ``author_name`` field.  The names are
not part of the content and are removed.

.. _sitemap: https://en.wikipedia.org/wiki/Site_map
