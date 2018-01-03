import re

import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class UsenixOrgSpider(FeedsSpider):
    name = 'usenix.org'
    allowed_domains = ['usenix.org']

    def feed_headers(self):
        return []

    def start_requests(self):
        yield scrapy.Request('https://www.usenix.org/publications/login',
                             self.parse_login_issues,
                             meta={'dont_cache': True})

    def parse_login_issues(self, response):
        # Only scrape the last 8 issues.
        issues = response.css('.issues .month a::attr(href)').extract()[:8]
        yield self.generate_feed_header(
            title=';login:', subtitle='The Usenix Magazine', link=response.url,
            path='login')
        for issue in issues:
            yield scrapy.Request(response.urljoin(issue),
                                 self.parse_login_issue)

    def parse_login_issue(self, response):
        remove_elems = [
            '.field-name-field-file-access',
            '.field-name-field-login-issue-file',
            '.field-name-field-product',
            '.field-commerce-price',
            '.views-field-field-file-access',
            '.view-header',
        ]
        il = FeedEntryItemLoader(response=response,
                                 base_url='https://www.{}'.format(self.name),
                                 remove_elems=remove_elems,
                                 dayfirst=True)
        il.add_value('link', response.url)
        title = response.css('h1::text').extract_first()
        il.add_value('title', title)
        il.add_value('updated', self._date_from_title(title))
        il.add_css('content_html', '.content-wrapper')
        il.add_value('path', 'login')
        if response.css('.usenix-files-protected'):
            il.add_value('category', 'paywalled')
        yield il.load_item()

    @staticmethod
    def _date_from_title(issue):
        """Try to guess the publication date of an issue from the title."""
        match = re.search(
            r'(?P<season>Spring|Summer|Fall|Winter) (?P<year>\d{4})', issue)
        if match:
            seasons = {'Spring': '03', 'Summer': '06', 'Fall': '09',
                       'Winter': '12'}
            month = seasons[match.group('season')]
            return '01-{month}-{year}'.format(
                month=month, year=match.group('year'))
