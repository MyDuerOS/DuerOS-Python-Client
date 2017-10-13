import tornado.httpserver
import tornado.ioloop
import tornado.web
import time
import json
import uuid
import requests
import datetime
import click

import dueros.config


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, output):
        self.config = dueros.config.load()
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
            dueros.config.save(self.config, configfile=self.output)

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


def login():
    application = tornado.web.Application([(r".*", MainHandler, dict(output=dueros.config.DEFAULT_CONFIG_FILE))])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(3000)
    tornado.ioloop.IOLoop.instance().start()
    tornado.ioloop.IOLoop.instance().close()

def main():
    try:
        import webbrowser
    except ImportError:
        print('Go to http://{your device IP}:3000 to start')
        login()
        return

    import threading
    webserver = threading.Thread(target=login)
    webserver.daemon = True
    webserver.start()
    print("A web page should is opened. If not, go to http://127.0.0.1:3000 to start")
    webbrowser.open('http://127.0.0.1:3000')

    while webserver.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
