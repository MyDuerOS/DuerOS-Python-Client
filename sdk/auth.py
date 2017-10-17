# -*- coding: utf-8 -*-
import tornado.httpserver
import tornado.ioloop
import tornado.web
import time
import json
import uuid
import requests
import datetime
import click

import sdk.configurate as configurate

# 开发者默认注册信息
CLIENT_ID = "5GFgMRfHOhIvI0B8AZB78nt676FeWA9n"
CLIENT_SECRET = "eq2eCNfbtOrGwdlA4vB1N1EaiwjBMu7i"


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, output, client_id, client_secret):
        self.config = configurate.load(client_id, client_secret)
        self.output = output

        self.token_url = 'https://openapi.baidu.com/oauth/2.0/token'
        self.oauth_url = 'https://openapi.baidu.com/oauth/2.0/authorize'

    @tornado.web.asynchronous
    def get(self):
        redirect_uri = self.request.protocol + "://" + self.request.host + "/authresponse"
        print '================request.path=', self.request.path
        if self.request.path == '/authresponse':
            code = self.get_argument("code")
            payload = {
                "client_id": self.config['client_id'],
                "client_secret": self.config['client_secret'],
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }

            r = requests.post(self.token_url, data=payload)
            config = r.json()
            print(r.text)
            self.config['refresh_token'] = config['refresh_token']

            if 'access_token' in config:
                date_format = "%a %b %d %H:%M:%S %Y"
                expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=config['expires_in'])
                self.config['expiry'] = expiry_time.strftime(date_format)
                self.config['access_token'] = config['access_token']

            print(json.dumps(self.config, indent=4))
            configurate.save(self.config, configfile=self.output)

            self.write('Succeed to login DuerOS Voice Service')
            self.finish()
            tornado.ioloop.IOLoop.instance().stop()
        else:
            payload = {
                "client_id": self.config['client_id'],
                "scope": 'basic',
                "response_type": "code",
                "redirect_uri": redirect_uri
            }

            req = requests.Request('GET', self.oauth_url, params=payload)
            p = req.prepare()
            print '============redirect url=', p.url
            self.redirect(p.url)


def login(client_id, client_secret):
    application = tornado.web.Application([(r".*", MainHandler,
                                            dict(output=configurate.DEFAULT_CONFIG_FILE, client_id=client_id,
                                                 client_secret=client_secret))])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(3000)
    tornado.ioloop.IOLoop.instance().start()
    tornado.ioloop.IOLoop.instance().close()


def auth_request(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    try:
        import webbrowser
    except ImportError:
        print('Go to http://{your device IP}:3000 to start')
        login(client_id, client_secret)
        return

    import threading
    webserver = threading.Thread(target=login, args=(client_id, client_secret))
    webserver.daemon = True
    webserver.start()
    print("A web page should is opened. If not, go to http://127.0.0.1:3000 to start")
    webbrowser.open('http://127.0.0.1:3000')

    while webserver.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
