import base64
import binascii
import hashlib
import io
import json
import os
import random
import re
import socket
import sys
import time
import zlib
from crypt import Crypter, Pkcs7Encoder
from hashlib import md5

import requests
import urllib3
from Crypto.Cipher import AES
from urllib3.exceptions import InsecureRequestWarning

from tools import rndDeviceId

urllib3.disable_warnings(InsecureRequestWarning)


def MD5(i):
    m = hashlib.md5()
    m.update(i.encode())
    return m.hexdigest()


class Activeuser():

    USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 7.0.0; SM-G955F Build/NRD90M)"
    USER_AGENT_HUB = "Mozilla/5.0 (Linux; Android 7.0.0; SM-G955F Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36"

    def __init__(self):
        self.encoder = Pkcs7Encoder()
        self.mode = AES.MODE_CBC
        self.s = requests.session()
        self.s.verify = False
        self.s.headers.update({'Content-Type': 'text/html', 'Accept-Language': 'en-gb',
                               'User-Agent': Activeuser.USER_AGENT})

    def get_ts(self):
        return str(int(time.time()))

    def call_api(self, data):
        ts = self.get_ts()
        key = self.get_key(ts)
        new_data = self.encrypt(data, key)
        r = self.s.post('https://activeuser.qpyou.cn/gateway.php', data=new_data, headers={
                        'REQ-TIMESTAMP': ts, 'REQ-AUTHKEY': self.makeAUTHKEY('%s:%s' % (new_data, ts))})
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

    USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 7.0.0; SM-G955F Build/NRD90M)"
    USER_AGENT_HUB = "Mozilla/5.0 (Linux; Android 7.0.0; SM-G955F Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36"

    def __init__(self, did=None, phone=None):
        self.s = requests.Session()
        self.s.verify = False
        if 'Admin-PC' == socket.gethostname():
            self.s.proxies.update(
                {'http': 'http://127.0.0.1:8888', 'https': 'https://127.0.0.1:8888', })
        self.s.headers.update({
            'User-Agent': QPYOU.USER_AGENT,
            'Accept-Language': 'en-gb'})
        self.did = did
        self.guest_uid = None
        #self.p1 = '{"hive_country":"EN","device_country":"EN","timezone":null,"language":"en","game_language":"eng",' \
        #          '"server_id":""}'
        self.p1 = '{"hive_country":"%s","device_country":"EN","timezone":null,"language":"en","game_language":"en", "server_id":""}'
        # self.p1 = '{"language":"en","timezone":null,"game_language":"en","server_id":"","device_country":"RU",' \
        #           '"hive_country":"RU"} '
        self.p2 = '{"hive_country":"EN","device_country":"EN","guest_uid":"%s","timezone":null,"language":"en",' \
                  '"game_language":"en","server_id":""}'
        self.phone = phone
        self._crypter = Crypter()
        self.getCountry()

    def getCountry(self):
        r = self.s.get('http://summonerswar-eu.com2us.net/api/location_c2.php')
        self.hive_country = json.loads(self._crypter.decrypt_response(r.content, 2))[
            'country_code']
        return self.hive_country

    def create(self):
        res = json.loads(self.s.post(
            'https://api.qpyou.cn/guest/create', data=self.p1 % (self.hive_country)).content)
        if res['error_code'] == 1401:
            print('ip banned')
            if socket.gethostname() == 'Admin-PC':
                return self.create()
            exit(1)
        self.guest_uid = res['guest_uid']
        return res

    def bind(self, guest_uid, hive_uid):
        res = json.loads(self.s.post(f"https://hub.qpyou.cn/guest/bind/{guest_uid}/{hive_uid}", data=self.p1 % (self.hive_country)).content)
        self.guest_uid = None
        return res

    def auth(self):
        return json.loads(self.s.post('https://api.qpyou.cn/guest/auth', data=self.p2 % (self.guest_uid)).content)

    def registered(self):
        return json.loads(self.s.post('https://api.qpyou.cn/device/registered', data=self.p1 % (self.hive_country)).content)

    def me(self):
        res = self.s2.post('https://api.qpyou.cn/user/me', data=self.p1 % (self.hive_country), headers={
            'Content-Type': 'application/json', 'Accept-Language': 'en-gb', 'User-Agent': QPYOU.USER_AGENT})
        # print(str(res.content))
        if 'thorization Faile' in str(res.content):
            return None
        return json.loads(res.content)

    def otpVerification(self, udata):
        if 'ct' not in udata and 'iv' not in udata and '"s"' not in udata and '"d"' not in udata:
            print('bad data')
            exit(1)
        r = self.s2.post('https://hub.qpyou.cn/otp/verification', data=udata, headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Origin': 'https://hub.qpyou.cn', 'X-Requested-With': 'XMLHttpRequest',
                                                                                       'User-Agent': QPYOU.USER_AGENT_HUB, 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'DNT': '1', 'Referer': 'https://hub.qpyou.cn/otp/main'})
        return json.loads(r.content)['result'] == 0

    def hiveLogin(self, user, password):
        native_ver = "Hive+v.2.6.7"
        if self.phone == 'xxx':
            ad_id = 'xxx'
            device = 'xxx'
            appid = 'com.com2us.smon.normal.freefull.google.kr.android.common'
            osversion = 'xxx'
            platform = 'android'
            vend_id = rndDeviceId()
        else:
            ad_id = rndDeviceId()
            device = 'SM-G955F'
            appid = 'com.com2us.smon.normal.freefull.google.kr.android.common'
            osversion = '7.0'
            platform = 'android'
            vend_id = rndDeviceId()
        self.s2 = requests.Session()
        self.s2.verify = False
        self.s2.headers.update({'Upgrade-Insecure-Requests': '1', 'User-Agent': QPYOU.USER_AGENT_HUB,
                                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'DNT': '1'})
        if 'Admin-PC' == socket.gethostname():
            self.s2.proxies.update(
                {'http': 'http://127.0.0.1:8888', 'https': 'https://127.0.0.1:8888', })
        s2r = self.s2.get('https://hub.qpyou.cn/auth')
        # print(s2r.content)
        if '/hub.qpyou.cn/auth/login_proc' not in s2r.content.decode():
            print('login page broken')
            exit(1)
        rr = self.s2.post('https://hub.qpyou.cn/auth/login_proc', data='id={}&password=&dkagh={}'.format(user, MD5(password)), headers={'Cache-Control': 'max-age=0', 'Origin': 'https://hub.qpyou.cn', 'Upgrade-Insecure-Requests': '1',
                                                                                                                                        'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': QPYOU.USER_AGENT_HUB, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'DNT': '1', 'Referer': 'https://hub.qpyou.cn/auth/login'})
        if '/otp/main' in rr.url:
            print('detected otp...')
            if 'class="join_otp"' in rr.content:
                _send_to = re.search(
                    'class="user_inform">(.*)</span>', rr.content).group(1)
                _udata = input(
                    'Open this: /otp/aes.html?mail=%s&code=123456 and paste the console log here:\n' % (_send_to))
                if self.otpVerification(_udata.rstrip()):
                    rr = self.s2.get('https://hub.qpyou.cn/otp/login', headers={'Cache-Control': 'max-age=0', 'Origin': 'https://hub.qpyou.cn', 'Upgrade-Insecure-Requests': '1', 'Content-Type': 'application/x-www-form-urlencoded',
                                                                                'User-Agent': QPYOU.USER_AGENT_HUB, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'DNT': '1', 'Referer': 'https://hub.qpyou.cn/otp/main'})
                    if '/gdpr/login' in rr.url:
                        rr = self.s2.post('https://hub.qpyou.cn/userinfo/gdpr/done', data='', headers={'Cache-Control': 'max-age=0', 'Origin': 'https://hub.qpyou.cn', 'Upgrade-Insecure-Requests': '1', 'Content-Type': 'application/x-www-form-urlencoded',
                                                                                                       'User-Agent': QPYOU.USER_AGENT_HUB, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'DNT': '1', 'Referer': 'https://hub.qpyou.cn/userinfo/gdpr/login'}, allow_redirects=False)
        self.s2.cookies.update({'gameindex': '2624', 'hive_config_language': 'en_US', 'inquiry_language': 'en_US', 'advertising_id': str(ad_id), 'appid': appid, 'device': device, 'did': str(
            random.randint(200000000, 300000000)) if not self.did else str(self.did), 'native_version': native_ver, 'osversion': osversion, 'platform': platform, 'vendor_id': vend_id})
        rr = self.s2.post('https://hub.qpyou.cn/auth/login_proc', data='id={}&password=&dkagh={}'.format(user, MD5(password)), headers={'Cache-Control': 'max-age=0', 'Origin': 'https://hub.qpyou.cn', 'Upgrade-Insecure-Requests': '1',
                                                                                                                                        'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': QPYOU.USER_AGENT_HUB, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'DNT': '1', 'Referer': 'https://hub.qpyou.cn/auth/login'}, allow_redirects=False)
        _uid = None
        if 'gdpr/login' in rr.headers['Location']:
            rr = self.s2.post('https://hub.qpyou.cn/userinfo/gdpr/done', data='', headers={'Cache-Control': 'max-age=0', 'Origin': 'https://hub.qpyou.cn', 'Upgrade-Insecure-Requests': '1', 'Content-Type': 'application/x-www-form-urlencoded',
                                                                                           'User-Agent': QPYOU.USER_AGENT_HUB, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8', 'DNT': '1', 'Referer': 'https://hub.qpyou.cn/userinfo/gdpr/login'}, allow_redirects=False)
        if 'c2shub://login?error_code' in rr.headers['Location']:
            sss = rr.headers['Location'].split('&')
            # print(rr.headers)
            _uid = sss[1].replace('uid=', '')
            sessionkey = sss[3].replace('sessionkey=', '')
            _did = sss[2].replace('did=', '')
            print(sss)
        if not _uid:
            return None
        return _uid, _did, sessionkey, appid

    def createNew(self):
        self.s.cookies.update(
            {'advertising_id': rndDeviceId(), 'appid': 'com.com2us.smon.normal.freefull.google.kr.android.common',
             'device': 'SM-G955F', 'did': str(random.randint(200000000, 300000000)) if not self.did else str(self.did),
             'native_version': 'Hive+v.2.6.7', 'osversion': '7.0', 'platform': 'android',
             'vendor_id': rndDeviceId()})
        self.registered()
        res = self.create()
        self.auth()
        return res['guest_uid'], res['did']
