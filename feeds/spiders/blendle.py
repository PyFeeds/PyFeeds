from base64 import b64decode
import json
import uuid

import scrapy

from feeds.exceptions import FeedsException


class BlendleAuthenticationError(FeedsException):
    pass


class BlendleSession:
    _spider = None
    _provider = None
    _subscription = False
    _jwt = None
    _username = None

    def __init__(self, spider, provider):
        self._spider = spider
        self._provider = provider

    def login(self, callback):
        login = self._spider.spider_settings.get('username')
        password = self._spider.spider_settings.get('password')
        if not (login and password):
            # Username, password or section not found in feeds.cfg.
            raise BlendleAuthenticationError(
                'Login failed: No username or password given. '
                'Only free articles are available in full text.'
            )
        credentials = json.dumps({
            'login': login,
            'password': password,
        })
        return scrapy.Request(
            url='https://pay.blendle.com/core/credentials',
            callback=self._after_login,
            errback=self._after_login,
            method='POST',
            body=credentials,
            meta={
                'handle_httpstatus_all': True,
                'callback': callback,
            },
            dont_filter=True,
        )

    def parse_article(self, response, item_jwt, callback_url, callback):
        if not self._subscription:
            # We do not have a valid subscription.
            # Fall back to parsing the original article.
            return callback(response)

        response.meta['blendle_callback_url'] = callback_url
        response.meta['callback'] = callback
        return scrapy.Request(
            url='https://pay.blendle.com/api/provider/{}/items'.format(
                self._provider),
            callback=self._parse_provider_item,
            method='POST',
            headers={'Content-Type': 'application/jwt'},
            body=item_jwt,
            meta=response.meta,
            dont_filter=True,
        )

    def _after_login(self, response):
        self._subscription = False

        if response.status != 200:
            if response.status in [500, 502, 503]:
                # Blendle is doing maintenance or is currently not available.
                logger = self._spider.logger.info
            else:
                logger = self._spider.logger.error
            logger('Login failed: Blendle returned status code {}'.format(
                response.status))
            return response.meta['callback']()

        try:
            self._jwt = json.loads(response.body_as_unicode())['jwt']
            # Fix padding by always adding too much of it.
            # Extraneous padding is ignored.
            self._username = json.loads(
                b64decode(self._jwt.split('.')[1] + '===').decode('utf-8')
            )['user_id']
            self._spider.logger.debug(
                'Successfully established Blendle session')
            self._subscription = True
        except json.decoder.JSONDecodeError:
            self._spider.logger.error(
                'Login failed: Could not parse response from Blendle')
        except KeyError:
            self._spider.logger.error(
                'Login failed: Username or password wrong')
        return response.meta['callback']()

    def _parse_provider_item(self, response):
        uid = json.loads(response.body.decode('utf-8'))['uid']
        uid = json.dumps({'uid': uid})
        return scrapy.Request(
            url='https://pay.blendle.com/api/user/{}/items'.format(
                self._username),
            callback=self._parse_user_item,
            method='POST',
            body=uid,
            headers={
                'Accept': 'application/jwt',
                'Authorization': 'Bearer {}'.format(self._jwt),
                'Content-Type': 'application/json',
            },
            meta=response.meta,
            dont_filter=True,
        )

    def _parse_user_item(self, response):
        # Now we have the token for the article and make the final request.
        pwb_token = response.body.decode('utf-8')
        return scrapy.Request(
            url=response.meta['blendle_callback_url'].format(
                cache_bust=uuid.uuid4()),
            headers={'X-Pwb-Token': pwb_token},
            callback=response.meta['callback'],
            meta=response.meta,
        )
