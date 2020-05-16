.. _API:

API for Spiders
===============
If you want to you support a custom website, take a look at
:ref:`Development`.

Spider class
------------
A spider is a class in a module (Python file) in ``feeds.spiders`` that is a
subclass of ``feeds.spiders.FeedsSpider``, ``feeds.spiders.FeedsCrawlSpider``
or ``feeds.spiders.FeedsXMLFeedSpider``.

  * ``FeedsXMLFeedSpider`` is used, if the spider is based on parsing an XML
    document as a basis. This is useful if the spider should start from an
    existing XML feed or a sitemap.
  * ``FeedsCrawlSpider`` is used, if the spider should crawl the site based on
    links that are found on the site. Patterns can be given to limit what
    links should be followed.
  * ``FeedsSpider`` is used in all other cases (this spider is usually used).

Class variables
^^^^^^^^^^^^^^^
  * ``name``: The name of the spider (**mandatory**).
  * ``start_urls``: A list of URLs to start (used if the
    ``start_requests(self)`` method is not overwritten).
  * ``feed_title``: Title of the feed.
  * ``feed_subtitle``: Subtitle of the feed.
  * ``feed_link``
  * ``author_name``: Author of the feed.
  * ``feed_icon``: URL of a site favicon.
  * ``feed_logo``: URL of a site logo.

Methods
^^^^^^^

  * ``start_requests(self)``: If the start request is more complicated than a
    simply ``GET`` to the URL(s) in the ``start_urls`` list, this method can
    be overwritten. It is expected to yield or return a ``scrapy.Request``
    object. Please note that this method can *only* emit ``Request`` objects.
  * ``parse(self, response)``: After a URL from ``start_urls`` has been
    scraped, the ``parse()`` method is called and the response is given as an
    argument.  It is also the default call back method for new
    ``scrapy.Request`` objects.
  * ``parse_node(self, response, node)``: A ``FeedsXMLFeedSpider`` calls
    ``parse_node()`` instead of ``parse()`` for every node in the XML document
    returned by the URL in ``start_urls``.


FeedEntryItemLoader
-------------------
A spider uses a ``FeedEntryItemLoader`` object to extract content from a
response. The following fields are accepted and can be added to a item loader
object:

    * ``link``
    * ``title``
    * ``author_name``
    * ``author_email``
    * ``content_html``
    * ``updated``
    * ``category``
    * ``path``
    * ``enclosure_iri``
    * ``enclosure_type``

A value can be added to an item loader with the ``add_value()``, ``add_css()``
or ``add_xpath()`` methods like in the following example:

.. code-block:: python

    il = FeedEntryItemLoader(response=response)
    il.add_value("link", response.url)
    il.add_css("title", "h1::text")
    il.add_css("author_name", "header .user-link__name::text")
    il.add_css("content_html", ".interview-body")
    il.add_css("updated", ".date::text")
    return il.load_item()

Only the ``link`` field is required, all the other fields can be empty but
usually it is adviced to add as many fields as possible (i.e. the original
site provides).

If the ``updated`` field is not provided, the date and time during the
extraction is used. If caching is enabled, the date and time when the item was
first seen is cached and reused on following runs.

Input processing
----------------
Automatic rules are applied to fields depending on their type.

Default input rules
^^^^^^^^^^^^^^^^^^^

These rules are usually applied to every field.

  #. Empty strings and ``None`` are skipped.
  #. The content is stripped.
  #. The content is unescaped twice, i.e. ``&amp;&xxx;`` is converted to its
     decoded (binary) equivalent.

``title``
^^^^^^^^^

  #. The default input rules apply.
  #. One title: "<title 1>"
  #. Two titles: "<title 1>: <title 2>"
  #. Three or more titles: "<title 1>: <title 2> - <title 3> - <title n>"

``updated``
^^^^^^^^^^^

  #. Empty strings and ``None`` are skipped.
  #. Unless the date is already a ``datetime`` object, it is parsed using
     ``dateutil.parser.parse()`` (with the year expected to be first, and the
     day *not* expected to be first).  If ``dateutil`` can't parse it because
     it's a human readable string, ``dateparser`` is used.  ``dayfirst``
     (default ``False``), ``yearfirst`` (default ``True``) and ``ignoretz``
     (default ``False``) can be set in the ``FeedEntryItemLoader``.
  #. If the ``datetime`` object is not already timezone aware, the timezone
     specified in the ``FeedEntryItemLoader`` is set.
  #. The first ``datetime`` object is used.

``author_name``
^^^^^^^^^^^^^^^

  #. The default input rules apply.
  #. Multiple author names are joined with ", " (comma and space) as a
     separator.

``path``
^^^^^^^^

  #. The default input rules apply.
  #. Multiple paths are joined with ``os.sep`` (e.g. ``/``) as a separator.

``content_html``
^^^^^^^^^^^^^^^^

  #. Empty strings and ``None`` are skipped.
  #. ``replace_regex`` in the ``FeedEntryItemLoader`` is a dict with
     ``pattern`` as a key and ``repl`` as a value. ``pattern`` and ``repl``
     are used as parameters for ``re.sub()``. ``pattern`` can be a string or
     a pattern object, ``repl`` a string or a function.
  #. ``convert_footnotes`` in the ``FeedEntryItemLoader`` is a list of CSS
     selectors which select footnotes or otherwise hidden text. Such elements
     are replaced with ``<small>`` elements and the text of the respective
     footnote in brackets.
  #. ``pullup_elems`` in the ``FeedEntryItemLoader`` is a dict with a CSS
     selector as a key and a distance as a value. A parent that is a given
     distance away from the selected element is replaced with the selected
     element. E.g. a distance of 1 means that the children replaces its parent.
  #. ``replace_elems`` in the ``FeedEntryItemLoader`` is a dict that contains a
     selector as a key and a string as a value. The selected element is
     replaced with the HTML fragment.
  #. ``remove_elems`` in the ``FeedEntryItemLoader`` is a list with CSS
     selectors of elements that should be removed.
  #. ``remove_elems_xpath`` in the ``FeedEntryItemLoader`` is a list with XPath
     queries of elements that should be removed.
  #. ``change_attribs`` in the ``FeedEntryItemLoader`` is a dict with a CSS
     selector as a key and a dict that describes how to change attribs as a
     value. The dict contains the old attrib name as a key and the new attrib
     name as a value. If the value is ``None``, the attrib is removed.
  #. ``change_tags`` in the ``FeedEntryItemLoader`` is a dict with a CSS
     selector as a key and a new tag name as a value. The tag name of the
     selected element is changed to the new tag name.
  #. Attributes ``class``, ``id`` and ones that start with ``data-`` are
     removed.
  #. Iframes are converted to a ``<div>`` that contains a link to the source of
     the iframe.
  #. Scripts, JavaScript, comments, styles and inline styles are removed.
  #. The HTML tree is flattened: Elements which do not have a text and are not
     supposed to be empty are removed. An element is replaced with is child if
     it has exactly one child and the child has the same tag.
  #. References in tags like ``<a>`` and ``<img>`` are made absolute.
