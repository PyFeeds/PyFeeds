import scrapy

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class KonsumentAtSpider(FeedsSpider):
    name = 'konsument.at'
    allowed_domains = ['konsument.at']
    start_urls = ['http://www.konsument.at/page/das-aktuelle-heft']

    _title = 'KONSUMENT.AT'
    _subtitle = 'Objektiv, unbestechlich, keine Werbung'
    _timezone = 'Europe/Vienna'

    def parse(self, response):
        user = self.spider_settings.get('username')
        pwd = self.spider_settings.get('password')
        if user and pwd:
            yield scrapy.FormRequest.from_response(
                response,
                formcss='#login form',
                formdata={'user': user,
                          'pwd': pwd},
                callback=self._after_login
            )
        else:
            # Username, password or section not found in feeds.cfg.
            self.logger.info('Login failed: No username or password given')
            # We can still try to scrape the free articles.
            yield from self._after_login(response)

    def _after_login(self, response):
        if 'login_failed' in response.body_as_unicode():
            self.logger.error('Login failed: Username or password wrong')
        for url in response.xpath(
                '//div[@id="content"]//a[text()!="Bestellen"]/@href'
                ).extract():
            yield scrapy.Request(response.urljoin(url),
                                 callback=self._parse_article_url)

    def _parse_article_url(self, response):
        if 'Fehler' in response.css('h2 ::text').extract_first():
            self.logger.info('Skipping {} as it returned an error'.format(
                             response.url))
            return

        remove_elems = ['div[style="padding-top:10px;"]']
        il = FeedEntryItemLoader(response=response,
                                 timezone=self._timezone,
                                 base_url='http://{}'.format(self.name),
                                 dayfirst=True,
                                 remove_elems=remove_elems)
        il.add_value('link', response.url)
        il.add_value('author_name', 'VKI')
        date = response.css('.issue').re_first(
            'veröffentlicht:\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})')
        il.add_value('updated', date)
        url = (response.xpath('//a[text()="Druckversion"]/@onclick').
               re_first(r"window\.open\('(.*)'\);"))
        il.add_css('title', 'h1::text')
        if url:
            yield scrapy.Request(response.urljoin(url),
                                 callback=self._parse_article,
                                 meta={'il': il})
        else:
            il.add_value('category', 'paywalled')
            il.add_css('content_html', '.primary')
            il.add_css('content_html', 'div[style="padding-top:10px;"] > h3')
            yield il.load_item()

    def _parse_article(self, response):
        remove_elems = ['#issue', 'h1', '#slogan', '#logo', '#footer']
        il = FeedEntryItemLoader(response=response,
                                 parent=response.meta['il'],
                                 base_url='http://{}'.format(self.name),
                                 remove_elems=remove_elems)
        il.add_css('content_html', '#page')
        yield il.load_item()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 smartindent autoindent
