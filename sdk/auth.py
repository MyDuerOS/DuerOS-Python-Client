# -*- coding: utf-8 -*-
'''
认证授权模块
'''
import tornado.httpserver
import tornado.ioloop
import tornado.web
import time
import json
import requests
import datetime

import sdk.configurate as configurate

# 开发者默认注册信息
CLIENT_ID = "5GFgMRfHOhIvI0B8AZB78nt676FeWA9n"
CLIENT_SECRET = "eq2eCNfbtOrGwdlA4vB1N1EaiwjBMu7i"

# 百度token服务器url
TOKEN_URL = 'https://openapi.baidu.com/oauth/2.0/token'
# 百度oauth服务器url
OAUTH_URL = 'https://openapi.baidu.com/oauth/2.0/authorize'


class MainHandler(tornado.web.RequestHandler):
    '''
    Tornado　webServer请求处理类
    '''

    def initialize(self, output, client_id, client_secret):
        '''
        处理类初始化
        :param output:配置文件保存地址
        :param client_id: 开发者注册信息
        :param client_secret: 开发者注册信息
        :return:
        '''
        self.config = configurate.load(client_id, client_secret)
        self.output = output

        self.token_url = TOKEN_URL
        self.oauth_url = OAUTH_URL

    @tornado.web.asynchronous
    def get(self):
        '''
        get 请求处理
        :return:
        '''
        redirect_uri = self.request.protocol + "://" + self.request.host + "/authresponse"
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

            # print(json.dumps(self.config, indent=4))
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
            self.redirect(p.url)


def login(client_id, client_secret):
    '''
    初始化Tornado　web server
    :param client_id: 开发者信息
    :param client_secret: 开发者信息
    :return:
    '''
    application = tornado.web.Application([(r".*", MainHandler,
                                            dict(output=configurate.DEFAULT_CONFIG_FILE, client_id=client_id,
                                                 client_secret=client_secret))])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(3000)
    tornado.ioloop.IOLoop.instance().start()
    tornado.ioloop.IOLoop.instance().close()


def auth_request(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    '''
    发起认证
    :param client_id:开发者注册信息
    :param client_secret: 开发者注册信息
    :return:
    '''
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
