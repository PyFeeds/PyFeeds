import json

from scrapy import Request
import bleach
import w3lib.url

from feeds.loaders import FeedEntryItemLoader
from feeds.spiders import FeedsSpider


class FacebookComSpider(FeedsSpider):
    name = 'facebook.com'
    allowed_domains = ['facebook.com']

    def feed_headers(self):
        return []

    def start_requests(self):
        app_id = self.spider_settings.get('app_id')
        app_secret = self.spider_settings.get('app_secret')
        if not (app_id and app_secret):
            self.logger.error('app_id and app_secret not found.')
            return
        access_token = '{app_id}|{app_secret}'.format(app_id=app_id,
                                                      app_secret=app_secret)

        for page_id in self.spider_settings.get('pages').split():
            url = 'https://graph.{name}/v2.10/{page_id}'.format(
                    name=self.name, page_id=page_id)
            url = w3lib.url.add_or_replace_parameter(url,
                                                     'access_token',
                                                     access_token)
            url = w3lib.url.add_or_replace_parameter(
                url, 'fields', ','.join([
                    'id', 'description', 'link', 'name',
                    'posts{' + ','.join([
                        'id', 'link', 'name', 'message', 'picture',
                        'status_type', 'type', 'created_time']) + '}'
                ]))
            yield Request(url, meta={'page_id': page_id, 'dont_cache': True})

    def parse(self, response):
        page = json.loads(response.text)
        yield self.generate_feed_header(title=page['name'], link=page['link'],
                                        path=response.meta['page_id'])
        for entry in page['posts']['data']:
            il = FeedEntryItemLoader()
            # updated_time also includes new comments not only updates to the
            # post.
            il.add_value('updated', entry['created_time'])
            il.add_value(
                'link',
                'https://www.{name}/{user_id}/posts/{post_id}'.format(
                    name=self.name,
                    **dict(zip(['user_id', 'post_id'], entry['id'].split('_')))
                ))
            message = entry.get('message')
            name = entry.get('name')
            link = entry.get('link')
            if message:
                message = message.splitlines()
                title = message[0]
                if len(title.split()) < 10 and not title.startswith('http'):
                    # If the first line has less than ten words, it could be a
                    # title.
                    if title.upper() == title:
                        title = title.title()
                    del message[0]
                elif name and not name.startswith('http'):
                    # Fallback to the name (of the link).
                    title = name
                else:
                    # Fallback to the first ten words of the message.
                    title = ' '.join(message[0].split(maxsplit=10)) + ' ...'
                message = bleach.linkify('</p><p>'.join(message))
                il.add_value('content_html', '<p>{}</p>'.format(message))
            elif name:
                title = name
            else:
                title = link
            il.add_value('title', title)
            if link and name:
                il.add_value('content_html',
                             '<p><a href="{link}">{name}</a></p>'.
                             format(link=link, name=name))
            picture = entry.get('picture')
            if picture:
                il.add_value('content_html',
                             '<a href="{link}"><img src="{image}"></a>'.
                             format(link=link, image=picture))
            il.add_value('path', response.meta['page_id'])
            yield il.load_item()
