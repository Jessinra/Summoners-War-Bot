from tools import rndDeviceId
from crypt import Pkcs7Encoder
import hashlib
import json
import random
import requests
import socket
import os
import urllib3
from Crypto.Cipher import AES
from hashlib import md5
import base64
import binascii
import io
import time
import sys
import zlib

from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)


def MD5(i):
    m = hashlib.md5()
    m.update(i)
    return m.hexdigest()


class Activeuser():
    def __init__(self):
        self.encoder = pkcs_seven_encoder()
        self.mode = AES.MODE_CBC
        self.s = requests.session()
        self.s.verify = False
        self.s.headers.update({'Content-Type': 'text/html', 'Accept-Language': 'en-gb', 'User-Agent':'SMON_Kr/3.8.5.38500 CFNetwork/808.2.16 Darwin/16.3.0'})

    def get_ts(self):
        return str(int(time.time()))

    def call_api(self, data):
        ts = self.get_ts()
        key = self.get_key(ts)
        new_data = self.encrypt(data, key)
        r = self.s.post('https://activeuser.qpyou.cn/gateway.php', data=new_data, headers={'REQ-TIMESTAMP': ts, 'REQ-AUTHKEY': self.makeAUTHKEY('%s:%s' % (new_data, ts))})
        return self.decode('{}: {}'.format(r.content, r.headers['REQ-TIMESTAMP']))

    def makeAUTHKEY(self, s):
        return self.get_md5(self.decode(s))

    def decode(self, s):
        encoded_data, ts = s.split(':')
        key = self.get_key(ts)
        return self.decrypt(encoded_data, key)

    def decrypt(self, s, key):
        e = AES.new(key, self.mode, '\x00'*16)
        return self.encoder.decode(e.decrypt(base64.b64decode(s)))

    def encrypt(self, s, key):
        e = AES.new(key, self.mode, '\x00'*16)
        return base64.b64encode(e.encrypt(self.encoder.encode(s)))

    def get_key(self, s):
        return self.get_md5(s)[:16]

    def get_md5(self, s):
        return md5(s).hexdigest()


class QPYOU(object):
    def __init__(self, did=None, phone=None):
        self.s = requests.Session()
        self.s.verify = False
        if 'Admin-PC' == socket.gethostname():
            self.s.proxies.update({'http': 'http://127.0.0.1:8888', 'https': 'https://127.0.0.1:8888', })
        self.s.headers.update({'Content-Type': 'application/json', 'Accept-Language': 'en-gb',
                               'User-Agent': 'Summoners%20War/3.8.6.38600 CFNetwork/808.2.16 Darwin/16.3.0'})
        self.did = did
        self.guest_uid = None
        self.p1 = '{"hive_country":"EN","device_country":"EN","timezone":null,"language":"en","game_language":"en",' \
                  '"server_id":""}'
        # self.p1 = '{"language":"en","timezone":null,"game_language":"en","server_id":"","device_country":"RU",' \
        #           '"hive_country":"RU"} '
        self.p2 = '{"hive_country":"EN","device_country":"EN","guest_uid":"%s","timezone":null,"language":"en",' \
                  '"game_language":"en","server_id":""}'
        self.phone = phone

    def create(self):
        res = json.loads(self.s.post('https://api.qpyou.cn/guest/create', data=self.p1).content)
        if res['error_code'] == 1401:
            print('ip banned')
            if socket.gethostname() == 'Admin-PC':
                return self.create()
            exit(1)
        self.guest_uid = res['guest_uid']
        return res

    def auth(self):
        return json.loads(self.s.post('https://api.qpyou.cn/guest/auth', data=self.p2 % self.guest_uid).content)

    def registered(self):
        return json.loads(self.s.post('https://api.qpyou.cn/device/registered', data=self.p1).content)

    def me(self):
        res = self.s.post('https://api.qpyou.cn/user/me', data=self.p1)
        # print(str(res.content))
        if 'thorization Faile' in str(res.content):
            return None
        return json.loads(res.content)

    def hiveLogin(self, user, password):
        if self.phone == 'xxx':
            ad_id = 'xxx'
            device = 'xxx'
            appid = 'com.com2us.smon.normal.freefull.google.kr.android.common'
            native_ver = 'Hive+v.2.6.6'
            osversion = 'xxx'
            platform = 'android'
            user_agent = 'xxx'
            vend_id = rndDeviceId()
        else:
            ad_id = '00000000-0000-0000-0000-000000000000'
            device = 'SM-G955F'
            appid = 'com.com2us.smon.normal.freefull.google.kr.android.common'
            native_ver = 'Hive+v.2.6.6'
            osversion = '7.0'
            platform = 'android'
            user_agent = 'Mozilla/5.0 (Linux; Android 7.0; SM-G955F Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, ' \
                         'like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36 '
            vend_id = rndDeviceId()
        self.s.cookies.update(
            {'hive_config_language':'en_US', 'hive_config_nationality':'CH', 'inquiry_language':'en_US', 'advertising_id': ad_id, 'appid': appid,
             'device': device, 'did': str(random.randint(200000000, 300000000)) if not self.did else str(self.did),
             'native_version': native_ver, 'osversion': osversion, 'platform': platform,
             'vendor_id': vend_id, 'gameindex': '2623', 'hive_source': 'C'})
        self.registered()
        r1 = self.s.post('https://hub.qpyou.cn/auth',
                         data='{"hive_country":"CH","device_country":"en","timezone":null,"language":"en",'
                         '"game_language":"en","server_id":""}',
                         allow_redirects=False)
        data = f'id={user}&password=&dkagh={MD5(password.encode('utf-8'))}'
        self.s.get('https://hub.qpyou.cn/auth/recent_account', cookies=r1.cookies)
        rr = self.s.post('https://hub.qpyou.cn/auth/login_proc', data=data,
                         headers={'Content-Type': 'application/x-www-form-urlencoded',
                                  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                  'User-Agent': user_agent,
                                  'Referer': 'https://hub.qpyou.cn/auth/login'}, allow_redirects=False)
        if '/otp/' in rr.headers['Location']:
            print('Detected otp...')
            self.s.get('https://hub.qpyou.cn/otp/main', 
                       headers={'Origin': 'https://hub.qpyou.cn',
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                                'User-Agent': user_agent,
                                'Accept-Language':'en-gb',
                                'Referer':'https://hub.qpyou.cn/auth/recent_account'})
            _udata = input('Open this: /otp/aes.html?mail=MYMAIL@MY.COM&code=123456 and paste the console log here')
            if 'ct' not in _udata and 'iv' not in _udata and '"s"' not in _udata and '"d"' not in _udata:
                print('Bad data')
                exit(1)
            self.s.post('https://hub.qpyou.cn/otp/verification', data=_udata)
            rr = self.s.get('https://hub.qpyou.cn/otp/login')
        sss = rr.headers['Location'].split('&')
        sessionkey = sss[3].replace('sessionkey=', '')
        _did = sss[2].replace('did=', '')
        res = self.me()
        if not res:
            return None
        return res['uid'], _did, sessionkey, appid

    def createNew(self):
        self.s.cookies.update(
            {'advertising_id': rndDeviceId(), 'appid': 'com.com2us.smon.normal.freefull.google.kr.android.common',
             'device': 'SM-G955F', 'did': str(random.randint(200000000, 300000000)) if not self.did else str(self.did),
             'native_version': 'Hive+v.2.6.6', 'osversion': '7.0', 'platform': 'android',
             'vendor_id': rndDeviceId()})
        self.registered()
        res = self.create()
        self.auth()
        return res['guest_uid'], res['did']
