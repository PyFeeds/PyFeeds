import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class AddendumOrgSpider(FeedsSpider):
    name = 'addendum.org'
    allowed_domains = [name]
    start_urls = ['https://www.addendum.org/projekte-ubersicht/']

    _title = 'Addendum'
    _subtitle = 'das, was fehlt'
    _link = 'https://www.{}'.format(name)
    _icon = ('https://www.{}/resources/dist/favicons/'
             'android-chrome-192x192.png').format(name)
    _timezone = 'Europe/Vienna'

    def parse(self, response):
        url = response.css('section::attr(data-url-project)').extract_first()
        yield scrapy.Request(url, self.parse_item, meta={'dont_cache': True})

    def parse_item(self, response):
        # First URL is the overview page.
        for url in (
                response.css('.projectNav__meta a::attr(href)').extract()[1:]):
            yield scrapy.Request(url, self._parse_article)

    def _parse_article(self, response):
        remove_elems = [
            '.projectNav', 'h1', '.socialMedia__headline', '.whyRead',
            '.overlayCTA', '.authors', '.socialMedia', '.sidebar',
            '.sectionBackground--colorTheme1', '.heroStage__copyright',
            '.heroStage__downLink', 'script', 'iframe', '.image__zoom ',
            '.image__copyrightWrapper'
        ]
        change_tags = {
            'div.heroStage__introText': 'strong',
            'figcaption': 'i',
            'figure': 'div'
        }
        replace_regex = {
            r'<span data-src="([^"]+)"></span>.*?' +
            r'<span data-src="([^"]+)" data-min-width="1000">':
            r'<a href="\2"><img src="\1"></a>',
            r'<div style=".*?"><video.*?></video>.*?</div></div>':
            '<em>Das eingebettete Video ist nur im Artikel verfügbar.</em>',
        }
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='https://www.{}'.format(self.name),
                                 remove_elems=remove_elems,
                                 change_tags=change_tags,
                                 replace_regex=replace_regex)
        il.add_value('link', response.url)
        il.add_value('author_name', 'Addendum')
        il.add_css('title', 'meta[property="og:title"]::attr(content)')
        il.add_css('updated',
                   'meta[property="og:updated_time"]::attr(content)')
        il.add_css('content_html', '.content')
        yield il.load_item()
