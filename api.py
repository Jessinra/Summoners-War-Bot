import itertools
import json
import logging
import math
import random
import socket
import time
from collections import OrderedDict
from random import randint
import ast
import random
import socket
import threading
from fake_useragent import UserAgent
import requests
import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning
from island_maps import IslandMaps

from crypt import Crypter
from mapping import dungeon_quest_map
from tools import isIn, list_to_dict, checkAndroidApk, updateDict, find

urllib3.disable_warnings(InsecureRequestWarning)


class API(object):
    def __init__(self, uid, did, id_=None, email=None, session=None, device=None, app_id=None, debug=0):
        self.logger = logging.getLogger('API')
        self.logger.setLevel(logging.INFO)
        self.fh = logging.FileHandler('log.log', 'w', encoding='utf-8')
        self.fh.setLevel(logging.INFO)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.fh.setFormatter(self.formatter)
        self.logger.addHandler(self.fh)
        self.debug = debug
        self.crypter = Crypter()
        self.s = requests.session()
        self.s.verify = False

        # if 'Admin-PC' == socket.gethostname():
        #     self.s.proxies.update({'http': 'http://127.0.0.1:8888', 'https': 'https://127.0.0.1:8888', })
        self.game_index = 2624
        self.proto_ver = 11080
        self.app_version = '3.8.0'
        net_version = self.app_version.split('.')
        net_version_str = ''.join(net_version)
        net_version_str = ''.join([net_version_str, '0' * (5 - len(net_version_str))])
        self.s.headers.update({'User-Agent': ''.join(['SMON_KR/', str(self.app_version), '.', net_version_str, ' CFNetwork/808.2.16 Darwin/16.3.0'])})
        if app_id and 'android' in str(app_id):
            sess_ver = requests.Session()
            headers = {'User-Agent': UserAgent().random, 'Host': 'play.google.com', 'Connection': 'keep-alive'}
            sess_ver.headers.update(headers)
            version_req = sess_ver.get('https://play.google.com/store/apps/details?id=' + app_id, allow_redirects=True, timeout=10).content
            soup = BeautifulSoup(version_req, "html.parser")
            version = None
            while not version:
                try:
                    version = soup.find('div', {'class': 'content', 'itemprop': 'softwareVersion'}).text.strip()
                except AttributeError:
                    self.log('Error retrieving recent app version, try again in 5s')
                    time.sleep(5)
                    version_req = sess_ver.get('https://play.google.com/store/apps/details?id=' + app_id, allow_redirects=True, timeout=10).content
                    soup = BeautifulSoup(version_req, 'html.parser')
            net_version = version.split('.')
            given_version = self.app_version.split('.')
            self.binary_size = 27464880
            self.binary_check = 'b3d5fa221101fb4c9e8184ad70c17c70'
            print(self.binary_check, self.binary_size)
            if len(version) > len(self.app_version) or any([int(net_version[i]) > int(given_version[i])
                                                            for i in range(len(net_version))]):
                self.app_version = version
                self.log('New app version found: {}'.format(version))
                self.log('For security reasons bot tries to download new android apk.')
                net_version_str = ''.join(net_version)
                net_version_str = net_version_str + '0' * (5 - len(net_version_str))
                self.s.headers.update({'User-Agent': 'SMON_KR/' + str(self.app_version) + '.' + net_version_str + ' CFNetwork/808.2.16 Darwin/16.3.0'})
                try:
                    self.binary_check, self.binary_size = checkAndroidApk()
                    self.log('MD5: {}, binary_size: {}'.format(self.binary_check, self.binary_size))
                except ConnectionError:
                    return
        elif app_id and 'ios' in str(app_id):
            version_req = requests.get('https://itunes.apple.com/de/app/summoners-war-sky-arena/id852912420').text
            soup = BeautifulSoup(version_req, "html.parser")
            version = None
            while not version:
                try:
                    version = soup.find('p', {'class': 'l-column small-6 medium-12 whats-new__latest__version'}).text.replace(
                        'Version', '').strip()
                except:
                    self.log('Error retrieving recent app version, try again in 5s')
                    time.sleep(5)
            net_version = version.split('.')
            given_version = self.app_version.split('.')
            if len(version) > len(self.app_version) or any([int(net_version[i]) > int(given_version[i])
                                                            for i in range(len(net_version))]):
                self.app_version = version
                self.log('New app version found: {}'.format(version))
                self.log('For security reasons bot stopped.')
                net_version_str = ''.join(net_version)
                net_version_str = net_version_str + '0' * (5 - len(net_version_str))
                self.s.headers.update({'User-Agent': 'SMON_KR/' + str(self.app_version) + '.' + net_version_str + ' CFNetwork/808.2.16 Darwin/16.3.0'})
                raise Exception()
        self.log('Current app version used: {}'.format(self.app_version))
        self.log('Header: {}'.format(self.s.headers))
        self.infocsv = None
        self.region = 'eu'
        self.c2_location = 'http://summonerswar-%s.com2us.net/api/location_c2.php'
        self.uid = int(uid)
        self.did = int(did)
        # data = DataHandler(api=self)
        self.isHive = False
        self.ts_val = 0
        self.session_start = time.time()
        self.device = device
        # self.mailList = None
        # self.scenario_list = None
        # self.dungeon_list = None
        # self.wizard_id = None
        # self.wizard_info = None
        # self.guild = None
        # self.shop_item_list = None
        # self.shop_interval_list = None
        # self.friend_list = None
        # self.helper_list = None
        # self.inventory_list = None
        # self.trial_tower_list = None
        # self.daily_quest_list = None
        # self.rune_list = None
        # self.unit_depository_slots = None
        # self.unit_list = None
        # self.defense_unit_list = None
        # self.wish_list = None
        # self.market_info = None
        # self.quest_active = None
        # self.buildings = None
        # self.deco_list = None
        # self.market_list = None
        # self.arena_list = None
        # self.arena_log = None
        # self.npc_list = None
        # self.daily_reward_info = None
        # self.user = None
        # self.pvp_info = None
        # self.idfa = None
        # self.worldboss_used_unit = None
        # self.worldboss_status = None
        self.c2_version = None
        self.c2_status = None
        self.c2_api = None
        self.last_position = {'island_id': 1,
                              'pos_x': 10,
                              'pos_y': 12}
        if id_ and email:
            self.log('hive account')
            self.id = id_
            self.email = email
            self.isHive = True
            self.session_key = session
        self.log('uid: {} did: {}'.format(uid, did))

    def is_bad_bot(self):
        self.is_bad_bot = True

    def set_can_refill(self):
        self.refill_energy = True

    def set_can_arena(self):
        self.can_arena = True

    def set_region(self, region=None):
        regions = ['gb', 'hub', 'jp', 'cn', 'sea', 'eu']
        '''
        gb = global
        eu = europe
        jp = japan
        sea = asia
        cn = china
        hub = ?
        '''
        if region not in regions:
            self.log('invalid region, choose one from these: {}'.format(','.join(regions)))
            # exit(1)
            self.region = random.choice(regions)
        self.region = region
        self.c2_location = self.c2_location % self.region

    def set_idfa(self, id_):
        self.idfa = id_

    def log(self, msg):
        print('[{}]: {}'.format(time.strftime('%H:%M:%S'), msg))
        try:
            self.logger.info(str(msg))
        except AttributeError:
            self.logger.info('None')

    def call_api(self, path, data, repeat=False):
        try:
            old_data = None
            if not repeat:
                if type(data) != str:
                    old_data = data
                    data = json.dumps(data, indent=1).replace(' ', '    ').replace(',   ', ',')
                    self._check_request_data(data)
                if self.debug:
                    self.log('Request: {}'.format(str(data)))
                data = self.crypter.encrypt_request(data, 2 if '_c2.php' in path else 1)
            ts = int(time.time())
            # print(str(self.crypter.get_player_server_connect_elapsed_time(ts)))
            try:
                res = self.s.post(path, data, headers={'SmonTmVal': str(old_data['ts_val']) if old_data else str(self.crypter.get_player_server_connect_elapsed_time(ts)), 'SmonChecker': self.crypter.get_smon_checker(data, ts)})
            except KeyError:
                return self.call_api(path, data, True)
            res = self.crypter.decrypt_response(res.content, 2 if '_c2.php' in path else 1)
            self._check_response_data(res)

            rj = json.loads(res)
            ret_val = self._check_ret_code(res, rj)
            # res = json.loads(res)
            if self.debug:
                self.log('Response: {}'.format(str(json.dumps(rj, indent=2))))
            time.sleep(0.5)
            return ret_val
        except Exception as e:
            self.log('Error when calling api: ' + str(e))
            raise e
            time.sleep(2)
            return self.call_api(path, data, True)

    def getLocation(self):
        regions = ['gb', 'hub', 'jp', 'cn', 'sea', 'eu']
        locations = json.loads(self.crypter.decrypt_response(self.s.get(self.c2_location).content,
                                                             2 if '_c2.php' in self.c2_location else 1))
        self.c2_status = locations['server_url_list'][regions.index(self.region)]['status']
        self.c2_version = locations['server_url_list'][regions.index(self.region)]['version']
        self.c2_api = locations['server_url_list'][regions.index(self.region)]['gateway']
        self.log('{} {} {} {}'.format(self.c2_location, self.c2_status, self.c2_version, self.c2_api))

    def getServerStatus(self):
        data = {'game_index': self.game_index, 'proto_ver': self.proto_ver, 'channel_uid': self.uid}
        return self.call_api(self.c2_status, data)

    def getVersionInfo(self):
        data = {'game_index': self.game_index, 'proto_ver': self.proto_ver, 'channel_uid': self.uid}
        res = self.call_api(self.c2_version, data)
        self.parseVersionData(res['version_data'])
        return res

    def parseVersionData(self, input_):
        for v in input_:
            if v['topic'] == 'protocol':
                self.log('found proto_ver: {}'.format(v['version']))
                self.proto_ver = int(v['version'])
            if v['topic'] == 'infocsv':
                self.log('found infocsv: {}'.format(v['version']))
                self.infocsv = v['version']

    def base_data(self, cmd, kind=1):
        data = OrderedDict()
        if kind == 1:
            data = OrderedDict([('command', cmd), ('game_index', self.game_index), ('session_key', self.getUID()),
                                ('proto_ver', self.proto_ver), ('infocsv', self.infocsv), ('channel_uid', self.uid)])
        elif kind == 2:
            # ts_val = int(round(self.ts_val + time.time() - self.session_start, 0))
            data = OrderedDict([('command', cmd), ('wizard_id', self.wizard_id), ('session_key', self.getUID()),
                                ('proto_ver', self.uid), ('infocsv', self.infocsv), ('channel_uid', self.uid),
                                ('ts_val', self.crypter.get_player_server_connect_elapsed_time())])
        return data

    def CheckLoginBlock(self):
        data = self.base_data('CheckLoginBlock')
        res = self.call_api(self.c2_api, data)
        return res

    def GetDailyQuests(self):
        data = self.base_data('GetDailyQuests', 2)
        res = self.call_api(self.c2_api, data)
        self.log(self.daily_quest_list)
        if res:
            self.UpdateDailyQuestById(16, 1)
        return res

    def GetDungeonList(self):
        data = self.base_data('GetDungeonList', 2)
        return self.call_api(self.c2_api, data)

    def GetInstanceList(self):
        data = self.base_data('getInstanceList', 2)
        return self.call_api(self.c2_api, data)

    def GetCostumeCollectionList(self):
        data = self.base_data('GetCostumeCollectionList', 2)
        return self.call_api(self.c2_api, data)

    def GetMiscReward(self):
        data = self.base_data('GetMiscReward', 2)
        return self.call_api(self.c2_api, data)

    def GetMailList(self):
        data = self.base_data('GetMailList', 2)
        return self.call_api(self.c2_api, data)

    def GetArenaLog(self):
        data = self.base_data('GetArenaLog', 2)
        return self.call_api(self.c2_api, data)

    def CheckDarkPortalStatus(self):
        data = self.base_data('CheckDarkPortalStatus', 2)
        return self.call_api(self.c2_api, data)

    def ReceiveDailyRewardSpecial(self):
        data = self.base_data('ReceiveDailyRewardSpecial', 2)
        return self.call_api(self.c2_api, data)

    def receiveDailyRewardInactive(self):
        data = self.base_data('receiveDailyRewardInactive', 2)
        return self.call_api(self.c2_api, data)

    def GetFriendRequest(self):
        data = self.base_data('GetFriendRequest', 2)
        return self.call_api(self.c2_api, data)

    def GetGuildInfo(self):
        data = self.base_data('GetGuildInfo', 2)
        return self.call_api(self.c2_api, data)

    def GetGuildSiegeStatusInfo(self):
        data = self.base_data('GetGuildSiegeStatusInfo', 2)
        return self.call_api(self.c2_api, data)

    def GetGuildSiegeParticipationInfo(self):
        data = self.base_data('GetGuildSiegeParticipationInfo', 2)
        return self.call_api(self.c2_api, data)

    def GetGuildSiegeParticipatedSiegeIdList(self):
        data = self.base_data('GetGuildSiegeParticipatedSiegeIdList', 2)
        return self.call_api(self.c2_api, data)

    def GetChatServerInfo(self):
        data = self.base_data('GetChatServerInfo', 2)
        return self.call_api(self.c2_api, data)

    def getMentorRecommend(self):
        data = self.base_data('getMentorRecommend', 2)
        return self.call_api(self.c2_api, data)

    def getRtpvpRejoinInfo(self):
        data = self.base_data('getRtpvpRejoinInfo', 2)
        return self.call_api(self.c2_api, data)

    def GetRTPvPInfo_v3(self):
        data = self.base_data('GetRTPvPInfo_v3', 2)
        return self.call_api(self.c2_api, data)

    def GetNoticeDungeon(self):
        data = self.base_data('GetNoticeDungeon', 2)
        return self.call_api(self.c2_api, data)

    def GetNoticeChat(self):
        data = self.base_data('GetNoticeChat', 2)
        return self.call_api(self.c2_api, data)

    def GetNpcFriendList(self):
        data = self.base_data('GetNpcFriendList', 2)
        return self.call_api(self.c2_api, data)

    def GetWizardInfo(self):
        data = self.base_data('GetWizardInfo', 2)
        return self.call_api(self.c2_api, data)

    def CheckDailyReward(self):
        data = self.base_data('CheckDailyReward', 2)
        return self.call_api(self.c2_api, data)

    def gettrialtowerupdateremained(self):
        data = self.base_data('gettrialtowerupdateremained', 2)
        return self.call_api(self.c2_api, data)

    def GetTrialTowerInfo_v2(self):
        data = self.base_data('GetTrialTowerInfo_v2', 2)
        return self.call_api(self.c2_api, data)

    def GetFriendList(self):
        data = self.base_data('GetFriendList', 2)
        return self.call_api(self.c2_api, data)

    def GetFriendRequestSend(self):
        data = self.base_data('GetFriendRequestSend', 2)
        return self.call_api(self.c2_api, data)

    def GetFriendRecommended(self):
        data = self.base_data('GetFriendRecommended', 2)
        return self.call_api(self.c2_api, data)

    def getUnitUpgradeRewardInfo(self):
        data = self.base_data('getUnitUpgradeRewardInfo', 2)
        return self.call_api(self.c2_api, data)

    def SetWizardName(self, name):
        self.log('new name: {}'.format(name))
        data = self.base_data('SetWizardName', 2)
        extra_data = OrderedDict([('wizard_name', name)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def OpenBlackMarketSlot(self):
        data = self.base_data('OpenBlackMarketSlot', 2)
        extra_data = OrderedDict([('building_id', self.buildings[11]['building_id'])])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def AcceptFriendRequest(self, req_wizard_id, req_wizard_name=''):
        self.log('Accepting friend request from: {}'.format(req_wizard_name if req_wizard_name else req_wizard_id))
        data = self.base_data('AcceptFriendRequest', 2)
        extra_data = OrderedDict([('req_wizard_id', req_wizard_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def AddFriendRequestByUid(self, uid, add_wizard_name=''):
        self.log('Sending friend request to: {}'.format(add_wizard_name if add_wizard_name else uid))
        data = self.base_data('AddFriendRequestByUid', 2)
        extra_data = OrderedDict([('uid', uid)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def AddFriendRequest(self, hub_id):
        self.log('Sending friend request to: {}'.format(hub_id))
        data = self.base_data('AddFriendRequest', 2)
        extra_data = OrderedDict([('hub_id', hub_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def SendDailyGift(self, friend_list):
        self.log('Sending social points to {}.'.format(friend_list))
        data = self.base_data('SendDailyGift', 2)
        extra_data = OrderedDict([('friend_list', friend_list)])
        data.update(extra_data)
        res = self.call_api(self.c2_api, data)
        if res:
            sent_to_number = len(friend_list)
            required = 5 - self.daily_quest_list[6]['progressed']
            self.UpdateDailyQuestById(6, min(sent_to_number, required))
        return res

    def GetBlackMarketList(self, crystal_refresh=False):
        self.log('Shop successfully refreshed.')
        data = self.base_data('GetBlackMarketList', 2)
        extra_data = OrderedDict(
            [('building_id', self.buildings[11]['building_id']), ('cash_used', int(crystal_refresh))])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def GetArenaWizardList(self, refresh=0, cash_used=0):
        self.log('Get enemies in arena.')
        data = self.base_data('GetArenaWizardList', 2)
        extra_data = OrderedDict([('refresh', refresh), ('cash_used', int(cash_used))])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def RewardDailyQuest(self, quest_id):
        self.log('Completing quest {}.'.format(quest_id))
        data = self.base_data('RewardDailyQuest', 2)
        extra_data = OrderedDict([('quest_id', quest_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BuyBlackMarketItem(self, item_no, item_master_type, item_master_id, amount):
        self.log('Buying item {} from magic shop'.format(item_no))
        data = self.base_data('BuyBlackMarketItem', 2)
        extra_data = OrderedDict([('building_id', self.buildings[11]['building_id']), ('item_no', int(item_no)),
                                  ('item_master_type', int(item_master_type)), ('item_master_id', int(item_master_id)),
                                  ('amount', int(amount))])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BuyInappProduct(self, product_id, product_price, currency, signature, receipt_data):
        data = self.base_data('BuyInappProduct', 2)
        extra_data = OrderedDict([('game_index', self.game_index), ('product_id', product_id),
                                  ('product_price', product_price), ('currency', currency),
                                  ('signature', signature), ('receipt_data', receipt_data)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def UpdateEventStatus(self, event_id):
        data = self.base_data('UpdateEventStatus', 2)
        extra_data = OrderedDict([('event_id', event_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def SellRune(self, rune_id_list):
        data = self.base_data('SellRune', 2)
        extra_data = OrderedDict([('rune_id_list', rune_id_list)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def GetEventTimeTable(self):
        data = self.base_data('GetEventTimeTable', 2)
        extra_data = OrderedDict([('lang', 1), ('app_version', self.app_version)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def Harvest(self, building_id):
        data = self.base_data('Harvest', 2)
        extra_data = OrderedDict([('building_id', building_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def TriggerShopItem(self, trigger_id):
        data = self.base_data('TriggerShopItem', 2)
        extra_data = OrderedDict([('trigger_id', trigger_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    """
    ach_list = [{'ach_id': , 'cond_id': , 'current': ,}]
    10401 = Fusionsinfos aufrufen
    10402 = Vero-Fusion aufrufen
    10403 = Feuer mon auf 3*
    10404 = Wasser mon auf 3*
    10405 = Wind mon auf 3*
    10406 = Feuer auf lvl 30
    10407 = wasser auf lvl 30
    10408 = wind auf lvl 30
    10409 = feuer erwecken
    10410 = wasser erwecken
    10411 = wind erwecken
    10412 = 1 fusion durchführen
    10413 = fusioniere succubus feuer
    10414 = fusioniere undine wasser
    10415 = fusioniere vampir wind
    10416 = fusioniere ifrit
    
    
    EVENT ID: 70011
    10606 = toa stage 30 -> do_toa(stage=30)
    10607 = toa stage 50 -> do_toa(stage=50)
    10608 = toa stage 70
    10609 = toa stage 100
    10610 = toah stage 70
    10611 = toah stage 100
    
    10612 = raid betreten
    10613 = raid clearen
    10618 = rang a in riss dungeon
    10614 = schleifsteine nutzen
    10619 = rang s in riss dungeon
    10615 = riss raid mit freundesunterstützung abschließen
    10620 = aufarbeitungsstein nutzen
    10616 = riss raid 3 oder höher clearen
    10621 = homunkulus beschwören
    10617 = riss raid 5 clearen
    10622 = alle riss dungeons mit s oder höher
    
    10601 = Etage 7 Dragons ohne Hilfe
    10602 = Etage 10 Dragons ohne Hilfe
    10603 = Etage 7 Dragons ohne Hilfe ohne Kristalle zu hitten
    10604 = Etage 7 Necro ohne Hilfe
    10605 = Necro 10 ohne Hilfe
    
    """
    def UpdateAchievement(self, ach_list):
        data = self.base_data('UpdateAchievement', 2)
        extra_data = OrderedDict([('ach_list', ach_list)])
        data.update(extra_data)

        with open('achievements.json', 'r', encoding='utf-8') as ach:
            achievements = json.load(ach)

        quests_to_activate = []
        for achievement in achievements:
            activate_list = []
            if int(achievement['quest id']) not in self.quest_active:
                prior_quests = ast.literal_eval(achievement['req id'])
                for quest in prior_quests:
                    if quest in self.quest_rewarded:
                        activate_list.append(True)
                    else:
                        if quest in [ach['ach_id'] for ach in ach_list]:
                            if self.quest_active[quest]['is_completed']:
                                activate_list.append(True)
                            else:
                                activate_list.append(False)
                        else:
                            activate_list.append(False)
                quests_to_activate.append({'quest_id': int(achievement['quest id'])})
        if quests_to_activate:
            self.ActivateQuests(quests_to_activate)

        return self.call_api(self.c2_api, data)

    """
    Aktiviert Quests nacheinander:
    10402 nach 10401
    10403, 10404, 10405 nach 10402
    10406 nach 10403
    10407 nach 10404
    10408 nach 10405
    10409 nach 10406
    10410 nach 10407
    10411 nach 10408
    10412 nach 10406, 10407, 10408
    10413, 10414, 10415 nach 10412
    10416 nach 10413, 10414, 10415
    
    10602 nach 10601
    10603 nach 10602
    10604 nach 10603
    10605 nach 10604
    
    10607 nach 10606
    10608 nach 10607
    10609 nach 10608
    10610 nach 10609
    10611 nach 10610
    
    10613, 10618 nach 10612
    10614 nach 10613
    10615 nach 10614
    10616 nach 10615
    10617 nach 10616
    10619 nach 10618
    10620 nach 10619
    10621 nach 10620
    10622 nach 10621
    """
    def ActivateQuests(self, quests):
        data = self.base_data('ActivateQuests', 2)
        extra_data = OrderedDict([('quests', quests)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def CleanObstacle(self, obstacle_id):
        data = self.base_data('CleanObstacle', 2)
        extra_data = OrderedDict([('obstacle_id', obstacle_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def createMentoring(self, target_wizard_id):
        data = self.base_data('createMentoring', 2)
        extra_data = OrderedDict([('target_wizard_id', target_wizard_id), ('type', 1), ('ignore_attend', 0)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def UpdateDailyQuest(self, quests):
        data = self.base_data('UpdateDailyQuest', 2)
        extra_data = OrderedDict([('quests', quests)])
        data.update(extra_data)
        res = self.call_api(self.c2_api, data)
        if res and sum([info['completed'] for quest, info in self.daily_quest_list.items()]) == len(
                self.daily_quest_list) - 1:
            self.UpdateDailyQuestById(1001, 1)
        return res

    def getUID(self):
        if self.isHive:
            return str(self.session_key)
        else:
            return str(self.uid)

    def GetArenaUnitList(self, opp_wizard_id):
        data = self.base_data('GetArenaUnitList', 2)
        extra_data = OrderedDict([('opp_wizard_id', opp_wizard_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def ExpandUnitDepositorySlot(self, cash_used):
        data = self.base_data('ExpandUnitDepositorySlot', 2)
        extra_data = OrderedDict([('cash_used', cash_used)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def ExpandUnitSlot(self, cash_used):
        data = self.base_data('ExpandUnitSlot', 2)
        extra_data = OrderedDict([('cash_used', cash_used)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BattleArenaStart(self, opp_wizard_id, unit_id_list, log_id=None):
        data = self.base_data('BattleArenaStart', 2)
        extra_data = OrderedDict([('opp_wizard_id', opp_wizard_id), ('unit_id_list', unit_id_list), ('retry', 0)])
        data.update(extra_data)
        if log_id:
            log_data = OrderedDict([('log_id', log_id)])
            data.update(log_data)
        res = self.call_api(self.c2_api, data)
        if res:
            self.UpdateDailyQuestById(8, 1)
        return res

    #
    # def BattleArenaStartRevenge(self, opp_wizard_id, unit_id_list, log_id):
    #     data = self.base_data('BattleArenaStart', 2)
    #     extra_data = OrderedDict([('opp_wizard_id', opp_wizard_id), ('unit_id_list', unit_id_list),
    # ('log_id', log_id),
    #          ('retry', 0)])
    #     data.update(extra_data)
    #     res = self.callAPI(self.c2_api, data)
    #     if res:
    #         self.UpdateDailyQuestById(8, 1)
    #     return res

    def BattleArenaResult(self, battle_key, opp_unit_status_list, unit_id_list, win_lose):
        data = self.base_data('BattleArenaResult', 2)
        extra_data = OrderedDict([('battle_key', battle_key), ('win_lose', win_lose),
                                  ('opp_unit_status_list', opp_unit_status_list), ('unit_id_list', unit_id_list),
                                  ('retry', 0)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BattleScenarioStart(self, region_id, stage_no, difficulty, unit_id_list, helper_list=None):
        helper_list = [helper_list[0]] if len(helper_list) >= 1 else []
        data = self.base_data('BattleScenarioStart', 2)
        extra_data = OrderedDict([('region_id', region_id), ('stage_no', stage_no), ('difficulty', difficulty),
                                  ('unit_id_list', unit_id_list), ('helper_list', helper_list),
                                  ('mentor_helper_list', '[]'),
                                  ('npc_friend_helper_list', '[]'), ('retry', '0')])
        data.update(extra_data)
        energy_before = self.wizard_info['wizard_energy']
        res = self.call_api(self.c2_api, data)
        energy_after = self.wizard_info['wizard_energy']
        cost = energy_before - energy_after
        if res:
            # Energy quest
            progressed = self.daily_quest_list[1]['progressed']
            self.UpdateDailyQuestById(1, min(cost, 20 - progressed))

            # Helper quest
            self.UpdateDailyQuestById(7, 1)
        return res

    def BattleDungeonStart(self, dungeon_id, stage_id, unit_id_list, helper_list=None):
        helper_list = [helper_list[0]] if len(helper_list) >= 1 else []
        data = self.base_data('BattleDungeonStart', 2)
        extra_data = OrderedDict([('dungeon_id', dungeon_id), ('stage_id', stage_id), ('helper_list', helper_list),
                                  ('mentor_helper_list', []), ('npc_friend_helper_list', []),
                                  ('unit_id_list', unit_id_list),
                                  ('cash_used', 0), ('retry', '0')])
        data.update(extra_data)
        energy_before = self.wizard_info['wizard_energy']
        res = self.call_api(self.c2_api, data)
        energy_after = self.wizard_info['wizard_energy']
        cost = energy_before - energy_after
        if res:
            # Energy quest
            progressed = self.daily_quest_list[1]['progressed']
            self.UpdateDailyQuestById(1, min(cost, 20 - progressed))

            # Helper quest
            self.UpdateDailyQuestById(7, 1)
        return res

    def BattleTrialTowerStart_v2(self, difficulty, floor_id, unit_id_list):
        data = self.base_data('BattleTrialTowerStart_v2', 2)
        extra_data = OrderedDict([('difficulty', difficulty), ('floor_id', floor_id), ('unit_id_list', unit_id_list),
                                  ('retry', 0)])
        data.update(extra_data)
        energy_before = self.wizard_info['wizard_energy']
        res = self.call_api(self.c2_api, data)
        energy_after = self.wizard_info['wizard_energy']
        cost = energy_before - energy_after
        if res:
            # Energy quest
            progressed = self.daily_quest_list[1]['progressed']
            self.UpdateDailyQuestById(1, min(cost, 20 - progressed))
        return res

    def BattleTrialTowerResult_v2(self, battle_key, difficulty, floor_id, win_lose, unit_id_list, opp_unit_status_list):
        data = self.base_data('BattleTrialTowerResult_v2', 2)
        extra_data = OrderedDict(
            [('battle_key', battle_key), ('difficulty', difficulty), ('floor_id', floor_id), ('win_lose', win_lose),
             ('unit_id_list', unit_id_list), ('opp_unit_status_list', opp_unit_status_list),
             ('island_id', self.last_position['island_id']), ('pos_x', self.last_position['pos_x']),
             ('pos_y', self.last_position['pos_y']), ('retry', 0)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BattleScenarioResult(self, battle_key, opp_unit_status_list, unit_id_list, position, clear_time, win_lose):
        data = self.base_data('BattleScenarioResult', 2)
        extra_data = OrderedDict([('battle_key', battle_key), ('win_lose', win_lose),
                                  ('opp_unit_status_list', opp_unit_status_list), ('unit_id_list', unit_id_list),
                                  ('position', position),
                                  ('clear_time', clear_time), ('retry', 0)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BattleDungeonResult(self, battle_key, dungeon_id, stage_id, unit_id_list, opp_unit_status_list, clear_time,
                            win_lose):
        data = self.base_data('BattleDungeonResult', 2)
        extra_data = OrderedDict([('battle_key', battle_key), ('dungeon_id', dungeon_id), ('stage_id', stage_id),
                                  ('win_lose', win_lose), ('unit_id_list', unit_id_list),
                                  ('opp_unit_status_list', opp_unit_status_list),
                                  ('island_id', self.last_position['island_id']),
                                  ('pos_x', self.last_position['pos_x']),
                                  ('pos_y', self.last_position['pos_y']), ('clear_time', clear_time), ('retry', 0)])
        data.update(extra_data)
        res = self.call_api(self.c2_api, data)
        if res and dungeon_id in list(dungeon_quest_map.keys()):
            self.UpdateDailyQuestById(dungeon_quest_map[dungeon_id], 1)
        return res

    def SummonUnit(self, mode):
        data = self.base_data('SummonUnit', 2)
        extra_data = OrderedDict([('building_id', self.buildings[2]['building_id']), ('mode', mode),
                                  ('pos_arr', [OrderedDict([('island_id', self.buildings[2]['island_id']),
                                                            ('pos_x', self.buildings[2]['pos_x']),
                                                            ('pos_y', self.buildings[2]['pos_y']),
                                                            ('unit_master_id', 0)])])])
        data.update(extra_data)
        res = self.call_api(self.c2_api, data)
        if res:
            self.UpdateDailyQuestById(3, len(res['unit_list']))
        return res

    def EquipRune(self, rune_id, unit_id):
        data = self.base_data('EquipRune', 2)
        extra_data = OrderedDict([('rune_id', rune_id), ('unit_id', unit_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def SetRecentDecks(self, deck_list):
        data = self.base_data('SetRecentDecks')

    def EquipRuneList(self, rune_id_list, unit_id):
        data = self.base_data('EquipRuneList', 2)
        extra_data = OrderedDict([('rune_id_list', rune_id_list), ('unit_id', unit_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    # Bedeutet Entwicklung
    def UpgradeRune(self, rune_id, upgrade_curr, cash_used=0, stone_used=0):
        data = self.base_data('UpgradeRune', 2)
        extra_data = OrderedDict([('rune_id', rune_id), ('upgrade_curr', upgrade_curr),
                                  ('cash_used', cash_used), ('stone_used', stone_used)])
        data.update(extra_data)
        res = self.call_api(self.c2_api, data)
        if res:
            self.UpdateDailyQuestById(4, 1)
        return res

    # Bedeutet Experience lvln
    def UpgradeDeco(self, deco_id):
        data = self.base_data('UpgradeDeco', 2)
        extra_data = OrderedDict([('deco_id', deco_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    """
    item_id: 900011=mysterious plant
    island_id: where to put object
    pos_x: where to put object
    pos_y where to put object
    """

    def BuyShopItem(self, item_id, island_id=0, pos_x=0, pos_y=0):
        self.log('{}'.format(self.shop_interval_list))
        data = self.base_data('BuyShopItem', 2)
        extra_data = OrderedDict([('item_id', item_id), ('island_id', island_id), ('pos_x', pos_x),
                                  ('pos_y', pos_y)])
        data.update(extra_data)
        self.log('{} {} {} {}'.format(item_id, island_id, pos_x, pos_y))
        return self.call_api(self.c2_api, data)

    def ClaimAchievementReward(self, ach_id):
        data = self.base_data('ClaimAchievementReward', 2)
        extra_data = OrderedDict([('ach_id', ach_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def SacrificeUnit(self, target_id, source_list, island_id, pos_x, pos_y, building_id=0):
        data = self.base_data('SacrificeUnit', 2)
        extra_data = OrderedDict([('target_id', target_id),
                                  ('island_id', island_id),
                                  ('building_id', building_id),
                                  ('pos_x', pos_x), ('pos_y', pos_y),
                                  ('source_list', source_list)])
        data.update(extra_data)
        res = self.call_api(self.c2_api, data)
        if res:
            self.UpdateDailyQuestById(2, 1)
            self.update_achievement_by_id(31, 1)
            self.update_achievement_by_id(188, 1)
            self.update_achievement_by_id(189, 1)
            self.update_achievement_by_id(190, 1)
            self.update_achievement_by_id(191, 1)
        return res

    def update_achievement_by_id(self, ach_id, increment=1):
        if ach_id in self.quest_active:
            if self.quest_active[ach_id]['is_completed'] != 1:
                try:
                    for condition in self.quest_active[ach_id]['conditions']:
                        self.UpdateAchievement([{'ach_id': ach_id, 'cond_id': condition[0],
                                                 'current': condition[1] + increment}])
                except KeyError:
                    pass

    def UpgradeUnit(self, target_id, source_list, island_id, pos_x, pos_y, building_id=0):
        data = self.base_data('UpgradeUnit', 2)
        extra_data = OrderedDict([('target_id', target_id), ('island_id', island_id),
                                  ('building_id', building_id),
                                  ('pos_x', pos_x), ('pos_y', pos_y),
                                  ('source_list', source_list)])
        data.update(extra_data)
        self.log('{} {} {} {} {} {}'.format(target_id, source_list, island_id, pos_x, pos_y, building_id))
        res = self.call_api(self.c2_api, data)
        if res:
            self.UpdateDailyQuestById(2, 1)
            self.update_achievement_by_id(31, 1)
            self.update_achievement_by_id(188, 1)
            self.update_achievement_by_id(189, 1)
            self.update_achievement_by_id(190, 1)
            self.update_achievement_by_id(191, 1)
        return res

    def UpdateDailyQuestById(self, quest_id, increment):
        try:
            if not self.daily_quest_list[quest_id]['completed']:
                progress = self.daily_quest_list[quest_id]['progressed'] + increment
                self.UpdateDailyQuest([{'quest_id': quest_id, 'progressed': progress}])
        except KeyError:
            self.log('Error updating quest: {}'.format(quest_id))

    def ReceiveMail(self, mail_id_list):
        data = self.base_data('ReceiveMail', 2)
        extra_data = OrderedDict([('mail_id_list', mail_id_list),
                                  ('island_id', self.last_position['island_id']),
                                  ('pos_x', self.last_position['pos_x']),
                                  ('pos_y', self.last_position['pos_y'])])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def WorldRanking(self):
        data = self.base_data('WorldRanking', 2)
        return self.call_api(self.c2_api, data)

    def DoRandomWishItem(self, crystal_refresh=False):
        data = self.base_data('DoRandomWishItem', 2)
        extra_data = OrderedDict([('island_id', self.buildings[10]['island_id']),
                                  ('building_id', self.buildings[10]['building_id']),
                                  ('pos_x', self.buildings[10]['pos_x']), ('pos_y', self.buildings[10]['pos_y']),
                                  ('cash_used', int(crystal_refresh))])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def GetRiftOfWorldsRaidServerInfo(self, join_type, raid_id, stage_id, speed=2, secret=1):
        data = self.base_data('GetRiftOfWorldsRaidServerInfo', 2)
        extra_data = OrderedDict([('join_type', join_type),
                                  ('raid_id', raid_id),
                                  ('stage_id', stage_id),
                                  ('speed', speed),
                                  ('secret', secret)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BattleRiftOfWorldsRaidStart(self, battle_key):
        data = self.base_data('BattleRiftOfWorldsRaidStart', 2)
        extra_data = OrderedDict([('battle_key', battle_key)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def BattleRiftOfWorldsRaidResult(self, battle_key, win_lose, opp_unit_status_list, user_status_list, clear_time, retry=0):
        data = self.base_data('BattleRiftOfWorldsRaidResult', 2)
        extra_data = OrderedDict([('battle_key', battle_key),
                                  ('win_lose', win_lose),
                                  ('opp_unit_status_list', opp_unit_status_list),
                                  ('user_status_list', user_status_list),
                                  ('clear_time', clear_time),
                                  ('retry', retry)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def do_raid(self):
        battle_start = self.GetRiftOfWorldsRaidServerInfo(1, 10001, 5, 2, 1)
        started = time.time()
        time.sleep(30)
        ended = time.time()
        battle_key = battle_start['tvalue'] + ended - started
        self.BattleRiftOfWorldsRaidStart(battle_key)
        clear_time = random.randint(180, 260)

    def GetWorldBossStatus(self, worldboss_id):
        data = self.base_data('GetWorldBossStatus', 2)
        extra_data = OrderedDict([('worldboss_id', worldboss_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def MoveUnitBuilding(self, move_list):
        data = self.base_data('MoveUnitBuilding', 2)
        extra_data = OrderedDict([('move_list', move_list)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def MoveFieldObject(self, island_id, object_type, object_id, pos_x, pos_y):
        data = self.base_data('MoveFieldObject', 2)
        extra_data = OrderedDict([('island_id', island_id), ('object_type', object_type), ('object_id', object_id),
                                  ('pos_x', pos_x), ('pos_y', pos_y)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def UpdateUnitExpGained(self, unit_id_list):
        data = self.base_data('UpdateUnitExpGained', 2)
        extra_data = OrderedDict([('unit_id_list', unit_id_list)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def LockUnit(self, unit_id):
        data = self.base_data('LockUnit', 2)
        extra_data = OrderedDict([('unit_id', unit_id)])
        data.update(extra_data)
        return self.call_api(self.c2_api, data)

    def _setUser(self, input_):
        self.user = input_
        # self.wizard_info = input_['wizard_info']
        self.wizard_id = input_['wizard_info']['wizard_id']
        # self.defense_unit_list = input_['defense_unit_list']
        self.log('wizard_id: {}'.format(self.wizard_id))
        # self.pvp_info = input_['pvp_info']
        # self.buildings = list_to_dict(self.user['building_list'], 'building_master_id')
        self.log('Buildings: {}'.format(self._getBuildings()))
        # self.deco_list = list_to_dict(self.user['deco_list'], 'master_id')
        self.log('Decos: {}'.format(self._getDecoList()))
        # self.scenario_list = input_['scenario_list']
        # self.unit_list = list_to_dict(input_['unit_list'], 'unit_id')
        # self.inventory_list = input_['inventory_info']
        # self.friend_list = list_to_dict(input_['friend_list'], 'wizard_id')
        # self.helper_list = list_to_dict(input_['helper_list'], 'wizard_id')
        # self.rune_list = list_to_dict(input_['runes'], 'rune_id')
        # self._parseUnitListRunes(self.unit_list)
        # self.shop_interval_list = list_to_dict(input_['shop_info']['interval_list'], 'item_id')
        # self.shop_item_list = list_to_dict(input_['shop_info']['item_list'], 'item_id')
        # self.quest_active = list_to_dict(input_['quest_active'], 'quest_id')
        self.log('Shop interval: {}'.format(self._getShopIntervalList()))
        self.log('Shop: {}'.format(self.shop_item_list))
        island_no = 1
        for island in self.island_info:
            if island['open'] == 1 and island['id'] != 100:
                island_no = island['id']
        self.island_list = IslandMaps(island_no)
        self.occupy_islands_deco()
        self.occupy_islands_buildings()
        self.occupy_islands_obstacles()

    def occupy_islands_deco(self):
        with open('decorations.json', 'r', encoding='utf-8') as deco:
            decorations = json.load(deco)
        for deco_, item in self.deco_list.items():
            index_found = find(decorations, 'deco master id', str(deco_))
            for x in range(int(decorations[index_found]['width'])):
                for y in range(int(decorations[index_found]['height'])):
                    self.island_list.update_occupation(item['island_id'], item['pos_x'] + x, item['pos_y'] + y, 1)

    def occupy_islands_buildings(self):
        with open('buildings.json', 'r', encoding='utf-8') as build:
            buildings = json.load(build)
        for build_, item in self.buildings.items():
            index_found = find(buildings, 'building master id', str(build_))
            for x in range(int(buildings[index_found]['width'])):
                for y in range(int(buildings[index_found]['height'])):
                    self.island_list.update_occupation(item['island_id'], item['pos_x'] + x, item['pos_y'] + y, 1)

    def occupy_islands_obstacles(self):
        with open('obstacles.json', 'r', encoding='utf-8') as obs:
            obstacles = json.load(obs)
        for obs_, item in self.obstacle_list.items():
            index_found = find(obstacles, 'obstacle master id', str(item['master_id']))
            for x in range(int(obstacles[index_found]['width'])):
                for y in range(int(obstacles[index_found]['height'])):
                    self.island_list.update_occupation(item['island_id'], item['pos_x'] + x, item['pos_y'] + y, 1)

    def _updateWizard(self, input_):
        self.wizard_info = input_

    def _updateGuild(self, input_):
        self.guild = input_

    def _update_unit_lock_list(self, input_):
        self.unit_lock_list = input_

    def _update_obstacle_list(self, input_):
        try:
            self.obstacle_list = updateDict(self.obstacle_list, input_, 'obstacle_id')
        except AttributeError:
            self.obstacle_list = updateDict(None, input_, 'obstacle_id')
        self.occupy_islands_obstacles()

    def _update_ts_val(self, input_):
        self.ts_val = input_
        self.session_start = time.time()

    def _update_worldboss_used_unit(self, input_):
        self.worldboss_used_unit = input_

    def _update_worldboss_status(self, input_):
        try:
            self.worldboss_status = updateDict(self.worldboss_status, input_, 'worldboss_id')
        except AttributeError:
            self.worldboss_status = updateDict(None, input_, 'worldboss_id')

    def _updateUnitDepositorySlots(self, input_):
        self.unit_depository_slots = input_

    def _updateDefenseUnitList(self, input_):
        self.defense_unit_list = input_

    def _update_quest_rewarded(self, input_):
        self.quest_rewarded = input_

    def _updateTrialTowerList(self, input_):
        try:
            self.trial_tower_list = updateDict(self.trial_tower_list, input_, 'difficulty')
        except AttributeError:
            self.trial_tower_list = updateDict(None, input_, 'difficulty')

    def _updateShopIntervalList(self, input_):
        try:
            self.shop_interval_list = updateDict(self.shop_interval_list, input_, 'item_id')
        except AttributeError:
            self.shop_interval_list = updateDict(None, input_, 'item_id')

    def _updateShopItemList(self, input_):
        try:
            self.shop_item_list = updateDict(self.shop_item_list, input_, 'item_id')
        except AttributeError:
            self.shop_item_list = updateDict(None, input_, 'item_id')
            # print(input_)

    def _updateNpcList(self, input_):
        try:
            self.npc_list = updateDict(self.npc_list, input_, 'wizard_id')
        except AttributeError:
            self.npc_list = updateDict(None, input_, 'wizard_id')

    def _updateQuestActive(self, input_):
        try:
            self.quest_active = updateDict(self.quest_active, input_, 'quest_id')
        except AttributeError:
            self.quest_active = updateDict(None, input_, 'quest_id')

    def _parseUnitListRunes(self, input_):
        if hasattr(self, 'rune_list'):
            for unit in input_:
                try:
                    self._updateRunes(input_[unit].get('runes'))
                except KeyError:
                    pass

    def _updateRunes(self, input_):
        try:
            self.rune_list = updateDict(self.rune_list, input_, 'rune_id')
        except AttributeError:
            self.rune_list = updateDict(None, input_, 'rune_id')

    def _updateRune(self, input_):
        try:
            self.rune_list = updateDict(self.rune_list, input_, 'rune_id')
        except AttributeError:
            self.rune_list = updateDict(None, input_, 'rune_id')

    def _removeRune(self, input_):
        if hasattr(self, 'rune_list'):
            for rune in input_:
                try:
                    self.rune_list.pop(rune)
                except KeyError:
                    pass

    def _updateArenaList(self, input_):
        self.arena_list = list_to_dict(input_, 'wizard_id')

    def _updateArenaLog(self, input_):
        self.arena_log = list_to_dict(input_, 'wizard_id')

    def _updatePvpInfo(self, input_):
        self.pvp_info = input_

    def _updateBuildings(self, input_):
        try:
            self.buildings = updateDict(self.buildings, input_, 'building_master_id')
        except AttributeError:
            self.buildings = updateDict(None, input_, 'building_master_id')
        self.occupy_islands_buildings()

    def _updateInventoryList(self, input_):
        self.inventory_list = input_

    def _updateFriendList(self, input_):
        self.friend_list = list_to_dict(input_, 'wizard_id')

    def _updateHelperList(self, input_):
        self.helper_list = list_to_dict(input_, 'wizard_id')

    def _updateGiftedFriends(self, input_):
        try:
            self.friend_list = updateDict(self.friend_list, input_, 'wizard_id')
        except AttributeError:
            self.friend_list = updateDict(None, input_, 'wizard_id')

    def _updateDailyQuestList(self, input_):
        try:
            self.daily_quest_list = updateDict(self.daily_quest_list, input_, 'quest_id')
        except AttributeError:
            self.daily_quest_list = updateDict(None, input_, 'quest_id')

    def _updateMailList(self, input_):
        self.mailList = list_to_dict(input_, 'mail_id')

    def _updateMarketList(self, input_):
        self.market_list = input_

    def _updateMarketInfo(self, input_):
        self.market_info = input_

    def _updateWishInfo(self, input_):
        self.wish_list = input_

    def _update_scenario_list(self, input_):
        self.scenario_list = input_

    def _update_dungeon_list(self, input_):
        self.dungeon_list = input_

    def _update_daily_reward_info(self, input_):
        self.daily_reward_info = input_

    def _remove_unit(self, input_):
        if hasattr(self, 'unit_list'):
            for unit in input_:
                self.unit_list.pop(unit['source_id'])

    def _update_deco_list(self, input_):
        try:
            self.deco_list = updateDict(self.deco_list, input_, 'master_id')
        except AttributeError:
            self.deco_list = updateDict(None, input_, 'master_id')
        self.occupy_islands_deco()

    def _update_unit_list(self, input_):
        try:
            self.unit_list = updateDict(self.unit_list, input_, 'unit_id')
        except AttributeError:
            self.unit_list = updateDict(None, input_, 'unit_id')

    def _getUserInfo(self):
        if hasattr(self, 'wizard_info'):
            return 'username: {}, level: {}, energy: {}, mana: {}, crystal: {}, honor point: {}, guild_point: {}, ' \
                   'social_points: {}, arena energy: {}'.format(self.wizard_info['wizard_name'],
                                                                self.wizard_info['wizard_level'],
                                                                self.wizard_info['wizard_energy'],
                                                                self.wizard_info['wizard_mana'],
                                                                self.wizard_info['wizard_crystal'],
                                                                self.wizard_info['honor_point'],
                                                                self.wizard_info['guild_point'],
                                                                self.wizard_info['social_point_current'],
                                                                self.wizard_info['arena_energy'])

    def _getBuildings(self):
        if hasattr(self, 'buildings'):
            return self.buildings

    def _get_unit_lock_list(self):
        if hasattr(self, 'unit_lock_list'):
            return self.unit_lock_list

    def _get_quest_rewarded(self):
        if hasattr(self, 'quest_rewarded'):
            return self.quest_rewarded

    def _get_obstacle_list(self):
        if hasattr(self, 'obstacle_list'):
            return self.obstacle_list

    def _get_shop_item_list(self):
        if hasattr(self, 'shop_item_list'):
            return self.shop_item_list

    def _get_ts_val(self):
        if hasattr(self, 'ts_val'):
            return self.ts_val

    def _get_worldboss_status(self):
        if hasattr(self, 'worldboss_status'):
            return self.worldboss_status

    def _get_worldboss_used_unit(self):
        if hasattr(self, 'worldboss_used_unit'):
            return self.worldboss_used_unit

    def _getGuild(self):
        if hasattr(self, 'guild'):
            return self.guild

    def _getDailyRewardInfo(self):
        if hasattr(self, 'daily_reward_info'):
            return self.daily_reward_info

    def _getDefenseUnitList(self):
        if hasattr(self, 'defense_unit_list'):
            return self.defense_unit_list

    def _getTrialTowerList(self):
        if hasattr(self, 'trial_tower_list'):
            return self.trial_tower_list

    def _getUnitDepositorySlots(self):
        if hasattr(self, 'unit_depository_slots'):
            return self.unit_depository_slots

    def _getQuestActive(self):
        if hasattr(self, 'quest_active'):
            return self.quest_active

    def _getShopIntervalList(self):
        if hasattr(self, 'shop_interval_list'):
            return self.shop_interval_list

    def _getPvpInfo(self):
        if hasattr(self, 'pvp_info'):
            return self.pvp_info

    def _getMailList(self):
        if hasattr(self, 'mailList'):
            return self.mailList

    def _getMarketList(self):
        if hasattr(self, 'market_list'):
            return self.market_list

    def _getMarketInfo(self):
        if hasattr(self, 'market_info'):
            return self.market_info

    def _getWishInfo(self):
        if hasattr(self, 'user'):
            return self.wish_list

    def _getNpcList(self):
        if hasattr(self, 'npc_list'):
            return self.npc_list

    def _getArenaList(self):
        if hasattr(self, 'arena_list'):
            return self.arena_list

    def _getArenaLog(self):
        if hasattr(self, 'arena_log'):
            return self.arena_log

    def _getScenarioList(self):
        if hasattr(self, 'scenario_list'):
            return self.scenario_list

    def _getDungeonList(self):
        if hasattr(self, 'dungeon_list'):
            return self.dungeon_list

    def _getDecoList(self):
        if hasattr(self, 'deco_list'):
            return self.deco_list

    def _getUnitList(self):
        if hasattr(self, 'unit_list'):
            return self.unit_list

    def _getRuneList(self):
        if hasattr(self, 'rune_list'):
            return self.rune_list

    def _getInventoryList(self):
        if hasattr(self, 'inventory_list'):
            return self.inventory_list

    def _getDailyQuestList(self):
        if hasattr(self, 'daily_quest_list'):
            return self.daily_quest_list

    def _getFriendList(self):
        if hasattr(self, 'friend_list'):
            return self.friend_list

    def _getHelperList(self):
        if hasattr(self, 'helper_list'):
            return self.helper_list

    def GuestLogin(self):
        data = OrderedDict([('command', 'GuestLogin'), ('game_index', self.game_index), ('proto_ver', self.proto_ver),
                            ('app_version', self.app_version), ('infocsv', self.infocsv), ('uid', self.uid),
                            ('channel_uid', self.uid), ('did', self.did), ('push', 1), ('is_emulator', 0),
                            ('country', 'DE'), ('lang', 'eng'), ('lang_game', 1), ('mac_address', '02:00:00:00:00:00'),
                            ('device_name', 'iPhone10,6'), ('os_version', '11.1'),
                            ('token', '0000000000000000000000000000000000000000000000000000000000000000'),
                            ('idfv', self.idfa), ('adid', '00000000-0000-0000-0000-000000000000'),
                            ('binary_size', 10448304), ('binary_check', '87c2986b797cfdf61e5816809395ad8d'),
                            ('create_if_not_exist', 1)])
        res = self.call_api(self.c2_api, data)
        self._setUser(res)
        self.log(self._getUserInfo())
        return res

    def login(self):
        self.getLocation()
        status = self.getServerStatus()['maintenace']
        while status == 1:
            wait_time = random.randint(250, 350)
            self.log('Server {} undergoing maintenance right now, waiting for {} seconds.'.format(self.region,
                                                                                                      wait_time))
            time.sleep(wait_time)
            status = self.getServerStatus()['maintenace']
        self.getVersionInfo()
        self.CheckLoginBlock()
        if self.isHive:
            res = self.HubUserLogin()
        else:
            res = self.GuestLogin()
        return res

    def HubUserLogin(self):
        if self.device == "xxx":
            device_name = 'xxx'
            os_version = 'xxx'
            mac = '02:00:00:00:00:00'
            token = ''
        else:
            device_name = 'SM-G955F'
            os_version = '7.0'
            mac = '02:00:00:00:00:00'
            token = '0000000000000000000000000000000000000000000000000000000000000000'
        data = OrderedDict([('command', 'HubUserLogin'), ('game_index', self.game_index), ('proto_ver', self.proto_ver),
                            ('app_version', self.app_version), ('session_key', self.session_key),
                            ('infocsv', self.infocsv), ('uid', self.uid), ('channel_uid', self.uid), ('did', self.did),
                            ('id', self.id), ('email', self.email), ('push', 1), ('is_emulator', 0), ('country', 'EN'),
                            ('lang', 'eng'), ('lang_game', 1), ('mac_address', mac),
                            ('device_name', device_name), ('os_version', os_version),
                            ('token', token), ('idfv', ''), ('adid', ''),
                            ('binary_size', self.binary_size), ('binary_check', self.binary_check),
                            ('create_if_not_exist', 0)])
        res = self.call_api(self.c2_api, data)
        self._setUser(res)
        self.log(self._getUserInfo())
        return res

    @staticmethod
    def parseBattleStart(input_, win_lose=1):
        battle_key = input_['battle_key']
        if win_lose:
            if 'opp_unit_list' in list(input_.keys()) and 'pvp_info' not in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_id'], 'result': 2} for item in
                                        itertools.chain.from_iterable(input_['opp_unit_list'])]
                return battle_key, opp_unit_status_list
            elif 'dungeon_unit_list' in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_id'], 'result': 2} for item in
                                        itertools.chain.from_iterable(input_['dungeon_unit_list'])]
                for alive_unit in opp_unit_status_list[-2:]:
                    alive_unit['result'] = 1
                return battle_key, opp_unit_status_list
            elif 'opp_unit_list' in list(input_.keys()) and 'pvp_info' in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_info']['unit_id'], 'result': 2} for item in
                                        input_['opp_unit_list']]
                return battle_key, opp_unit_status_list
            elif 'trial_tower_unit_list' in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_id'], 'result': 2} for item in
                                        itertools.chain.from_iterable(input_['trial_tower_unit_list'])]
                return battle_key, opp_unit_status_list
        else:
            if 'opp_unit_list' in list(input_.keys()) and 'pvp_info' not in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_id'], 'result': 2} for item in
                                        itertools.chain.from_iterable(input_['opp_unit_list'])]
                opp_unit_status_list[-1]['result'] = 1
                return battle_key, opp_unit_status_list
            elif 'dungeon_unit_list' in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_id'], 'result': 2} for item in
                                        itertools.chain.from_iterable(input_['dungeon_unit_list'])]
                for alive_unit in opp_unit_status_list[-3:]:
                    alive_unit['result'] = 1
                return battle_key, opp_unit_status_list
            elif 'opp_unit_list' in list(input_.keys()) and 'pvp_info' in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_info']['unit_id'], 'result': 2} for item in input_['opp_unit_list']]
                opp_unit_status_list[-1]['result'] = 1
                return battle_key, opp_unit_status_list
            elif 'trial_tower_unit_list' in list(input_.keys()):
                opp_unit_status_list = [{'unit_id': item['unit_id'], 'result': 1 if item['boss'] == 1 else 2}
                                        for item in itertools.chain.from_iterable(input_['trial_tower_unit_list'])]
                return battle_key, opp_unit_status_list

    def parseBattleResult(self, input_):
        self.log('Battle finished, win: {}'.format(input_['win_lose']))
        self.log('Rewards: {}'.format(input_['reward']))

    def doDungeon(self, dungeon_id, stage_id, clear_time, units=None, helper_list=None, win_lose=1):
        if dungeon_id not in [dungeon['dungeon_id'] for dungeon in self.dungeon_list]:
            self.log('Dungeon {} does not exist or isn\'t available today.'.format(dungeon_id))
            return
        unit_id_list = [{'unit_id': unit['unit_id']} for unit in
                        self.defense_unit_list] if not units else units
        helper_list = [] if not helper_list else helper_list
        # unit_id_list.sort()
        # self.log('{} {} {} {}'.format(dungeon_id, stage_id, unit_id_list, helper_list))
        self.log('{}'.format(helper_list))
        dungeon_start = self.BattleDungeonStart(dungeon_id, stage_id, unit_id_list, helper_list)
        if not dungeon_start:
            self.log('Dungeon: {}, stage: {} not successfully started'.format(dungeon_id, stage_id))
            return
        battley_key, opp_unit_status_list = API.parseBattleStart(dungeon_start, win_lose)
        time.sleep(clear_time)
        dungeon_end = self.BattleDungeonResult(battley_key, dungeon_id, stage_id, unit_id_list, opp_unit_status_list,
                                               clear_time, win_lose)
        self.parseBattleResult(dungeon_end)
        time.sleep(3)

    def doArena(self, opp_wizard_id, units=None, win_lose=1, log_id=0, is_npc=False):
        if opp_wizard_id not in [wizard for wizard in self.arena_list] \
                and opp_wizard_id not in [wizard for wizard in self.arena_log] \
                and not is_npc:
            self.log('No valid opponent to battle.')
            return
        if opp_wizard_id in [wizard for wizard in self.arena_log]:
            log_id = self.arena_log[opp_wizard_id]['log_id']
        unit_id_list = [{'unit_id': unit['unit_id']} for unit in
                        self.defense_unit_list] if not units else units[:4]
        arena_start = self.BattleArenaStart(opp_wizard_id, unit_id_list, log_id) if log_id else self.BattleArenaStart(
            opp_wizard_id, unit_id_list)
        if not arena_start:
            self.log('Battle not successfully started.')
            return
        battle_key, opp_unit_status_list = API.parseBattleStart(arena_start, win_lose)
        time.sleep(random.randint(30, 40))
        arena_end = self.BattleArenaResult(battle_key, opp_unit_status_list, unit_id_list, win_lose)
        self.parseBattleResult(arena_end)
        time.sleep(3)

    def doToa(self, difficulty, floor_id, clear_time, units=None, win_lose=1):
        if 100 >= floor_id > self.trial_tower_list[difficulty]['cleared'] + 1:
            self.log('Invalid floor id {} for toa.'.format(floor_id))
            return
        unit_id_list = [{'unit_id': unit['unit_id']} for unit in self.defense_unit_list] if not units else units
        battle_start = self.BattleTrialTowerStart_v2(difficulty, floor_id, unit_id_list)
        if not battle_start:
            self.log('Battle not successfully started.')
            return
        battle_key, opp_unit_status_list = API.parseBattleStart(battle_start, win_lose)
        time.sleep(clear_time)
        battle_end = self.BattleTrialTowerResult_v2(battle_key, difficulty, floor_id, win_lose, unit_id_list, opp_unit_status_list)
        self.parseBattleResult(battle_end)
        time.sleep(3)

    def do_scenario(self, region_id, stage_no, difficulty, clear_time, units=None, helper_list=None, win_lose=1):
        with open('scenarios.json', 'r', encoding='utf-8') as scen:
            scenarios = json.load(scen)
        print(region_id)
        print(self.scenario_list)
        if str(region_id) not in [scenario['region id'] for scenario in scenarios]:
            self.log('Region {} does not exist.'.format(region_id))
            return False
        if difficulty not in range(1, 4):
            self.log('Given difficulty {} is not valid.'.format(difficulty))
            return False
        if stage_no not in range(1, 8):
            self.log('Given stage number {} is not valid.'.format(stage_no))
            return False
        # if [difficulty, region_id] not in [[scenario['difficulty'], scenario['region id']] for scenario in scenarios]:
        #     self.log(
        #         'No valid region / difficulty variation found with given parameters. Region: {}, difficulty: {}'.format(
        #             region_id, difficulty))
        #     return False

        if any([region['region_id'] == region_id and region['difficulty'] == difficulty
                and region['stage_list'][-1]['stage_no'] + 1 < stage_no for region in self.scenario_list]):
            self.log('Not able to skip levels.')
            return False

        scenario_id = str(region_id) + '0' + str(difficulty) + '0' + str(stage_no)

        if self.wizard_info['wizard_energy'] < int(scenarios[find(scenarios, 'scenario id', scenario_id)]['energy cost']):
            self.log('Not enough energy.')
            return False

        unit_id_list = [{'unit_id': unit['unit_id']} for unit in self.defense_unit_list] if not units else units
        helper_list = [] if not helper_list else helper_list
        # unit_id_list.sort()
        # self.log('{} {} {} {} {}'.format(region_id, stage_no, difficulty, unit_id_list, helper_list))
        battle_start = self.BattleScenarioStart(region_id, stage_no, difficulty, unit_id_list, helper_list)
        if not battle_start:
            self.log('Battle not successfully started.')
            return False
        res = API.parseBattleStart(battle_start, win_lose)
        self.log('Battle started: region {}, stage {}, difficulty {}'.format(region_id, stage_no, difficulty))
        unit_result_list = [{'unit_id': unit['unit_id'], 'pos_id': i + 1} for i, unit in enumerate(unit_id_list)]
        time.sleep(clear_time)
        # self.log('{} {} {} {} {} {}'.format(res[0], res[1], unit_id_list,
        #                                        {"island_id": self.last_position['island_id'],
        #                                         "pos_x": self.last_position['pos_x'],
        #                                         "pos_y": self.last_position['pos_y']}, clear_time, win_lose))
        battle_end = self.BattleScenarioResult(res[0], res[1], unit_result_list,
                                               {"island_id": self.last_position['island_id'],
                                                "pos_x": self.last_position['pos_x'],
                                                "pos_y": self.last_position['pos_y']}, clear_time, win_lose)
        self.parseBattleResult(battle_end)
        time.sleep(3)
        return True

    def remove_all_obstacles(self):
        for obstacle in self.user['obstacle_list']:
            self.CleanObstacle(obstacle['obstacle_id'])

    def _check_response_data(self, res):
        if isIn('island_info', res):
            try:
                self.island_info = json.loads(res)['island_info']
                island_no = 1
                for island in self.island_info:
                    if island['open'] == 1 and island['id'] != 100:
                        island_no = island['id']
                self.island_list = IslandMaps(island_no)
            except KeyError:
                self.log('Error logging island_info')
                self.log(json.loads(res))
        if isIn('scenario_info', res):
            try:
                input_ = json.loads(res)['scenario_info']
                region_list = [{'i': i, 'region': region} for i, region in enumerate(self.scenario_list) if region['region_id'] == input_['region_id'] and region['difficulty'] == input_['difficulty']]
                if region_list:
                    for region in region_list:
                        self.scenario_list[region['i']]['stage_list'][input_['stage_no']-1]['cleared'] = input_['cleared']
                        if input_['stage_no'] == 7 and input_['cleared'] == 1:
                            self.scenario_list[region['i']]['cleared'] = 1
                else:
                    stage_list = [{'stage_no': i, 'cleared': 0} for i in range(1, 8)]
                    stage_list[input_['stage_no']]['cleared'] = input_['cleared']
                    self.scenario_list.append({'region_id': input_['region_id'], 'difficulty': input_['difficulty'],
                                               'cleared': 0, 'stage_list': stage_list})
                self.log(self._getScenarioList())
            except KeyError:
                self.log('Error logging scenario_info')
                self.log(json.loads(res))
        if isIn('reward_info', res):
            try:
                self.log(self._getQuestActive())
                self.log(self._get_quest_rewarded())
                self.log(json.loads(res)['reward_info']['quest_id'])
                self.quest_active.pop(json.loads(res)['reward_info']['quest_id'])
                self.quest_rewarded.append(json.loads(res)['reward_info']['quest_id'])
                self.log(self._getQuestActive())
                self.log(self._get_quest_rewarded())
            except KeyError:
                self.log('Error logging reward_info')
                self.log(json.loads(res))
        if isIn('unit_lock_list', res):
            try:
                self._update_unit_lock_list(json.loads(res)['unit_lock_list'])
                self.log(self._get_unit_lock_list())
            except KeyError:
                self.log('Error logging unit_lock_list')
                self.log(json.loads(res))
        if isIn('quest_rewarded', res):
            try:
                self._update_quest_rewarded(json.loads(res)['quest_rewarded'])
                self.log(self._get_quest_rewarded())
            except KeyError:
                self.log('Error logging quest_rewarded')
                self.log(json.loads(res))
        if isIn('obstacle_list', res):
            try:
                self._update_obstacle_list(json.loads(res)['obstacle_list'])
                self.log(self._get_obstacle_list())
            except KeyError:
                self.log('Error logging obstacle_list')
                self.log(json.loads(res))
        if isIn('obstacle_info', res):
            try:
                self._update_obstacle_list(json.loads(res)['obstacle_info'])
                self.log(self._get_obstacle_list())
            except KeyError:
                self.log('Error logging obstacle_info')
                self.log(json.loads(res))
        if isIn('wizard_info', res):
            try:
                self._updateWizard(json.loads(res)['wizard_info'])
                self.log(self._getUserInfo())
            except KeyError:
                self.log('Error logging wizard_info')
                self.log(json.loads(res))
        if isIn('ts_val', res):
            try:
                self._update_ts_val(json.loads(res)['ts_val'])
                self.log(self._get_ts_val())
            except KeyError:
                self.log('Error logging ts_val')
                self.log(json.loads(res))
        if isIn('worldboss_status', res):
            try:
                self._update_worldboss_status(json.loads(res)['worldboss_status'])
                self.log(self._get_worldboss_status())
            except KeyError:
                self.log('Error logging worldboss_status')
                self.log(json.loads(res))
        if isIn('npc_list', res):
            try:
                self._updateNpcList(json.loads(res)['npc_list'])
                self.log(self._getNpcList())
            except KeyError:
                self.log('Error logging npc_list')
                self.log(json.loads(res))
        if isIn('wish_list', res):
            try:
                self._updateWishInfo(json.loads(res)['wish_list'])
                self.log(self._getWishInfo())
            except KeyError:
                self.log('Error logging wish_list')
                self.log(json.loads(res))
        if isIn('guild', res):
            try:
                self._updateGuild(json.loads(res)['guild'])
                self.log(self._getGuild())
            except KeyError:
                self.log('Error logging guild')
                self.log(json.loads(res))
        if isIn('worldboss_used_unit', res):
            try:
                self._update_worldboss_used_unit(json.loads(res)['worldboss_used_unit'])
                self.log(self._get_worldboss_used_unit())
            except KeyError:
                self.log('Error logging worldboss_used_unit')
                self.log(json.loads(res))
        if isIn('defense_unit_list', res):
            try:
                self._updateDefenseUnitList(json.loads(res)['defense_unit_list'])
                self.log(self._getDefenseUnitList())
            except KeyError:
                self.log('Error logging defense_unit_list')
                self.log(json.loads(res))
        if isIn('trial_tower_list', res):
            try:
                self._updateTrialTowerList(json.loads(res)['trial_tower_list'])
                self.log(self._getTrialTowerList())
            except KeyError:
                self.log('Error logging trial_tower_list')
                self.log(json.loads(res))
        if isIn('shop_interval_info', res):
            try:
                self._updateShopIntervalList(json.loads(res)['shop_interval_info'])
                self.log(self._getShopIntervalList())
            except KeyError:
                self.log('Error logging shop_interval_info')
                self.log(json.loads(res))
        if isIn('interval_list', res):
            try:
                self._updateShopIntervalList(json.loads(res)['shop_info']['interval_list'])
                self.log(self._getShopIntervalList())
            except KeyError:
                self.log('Error logging interval_list')
                self.log(json.loads(res))

        if isIn('target_unit', res):
            try:
                self._update_unit_list(json.loads(res)['target_unit'])
                self.log(self._getUnitList())
            except KeyError:
                self.log('Error logging target_unit')
                self.log(json.loads(res))
        if isIn('deco_info', res):
            try:
                self._update_deco_list(json.loads(res)['deco_info'])
                self.log(self._getDecoList())
            except KeyError:
                self.log('Error logging deco_info')
                self.log(json.loads(res))
        if isIn('building_info', res):
            try:
                self._updateBuildings(json.loads(res)['building_info'])
                self.log(self._getBuildings())
            except KeyError:
                self.log('Error logging building_info')
                self.log(json.loads(res))
        if isIn('deco_list', res):
            try:
                self._update_deco_list(json.loads(res)['deco_list'])
                self.log(self._getDecoList())
            except KeyError:
                self.log('Error logging deco_list')
                self.log(json.loads(res))
        if isIn('quest_active', res):
            try:
                self._updateQuestActive(json.loads(res)['quest_active'])
                self.log(self._getQuestActive())
            except KeyError:
                self.log('Error logging quest_active')
                self.log(json.loads(res))
        if isIn('item_list', res):
            try:
                self._updateShopItemList(json.loads(res)['shop_info']['item_list'])
                self.log(self._get_shop_item_list())
            except KeyError:
                self.log('Error logging item_list')
                self.log(json.loads(res))
        if isIn('achievement_list', res):
            try:
                self._updateQuestActive(json.loads(res)['achievement_list'])
                self.log(self._getQuestActive())
            except KeyError:
                self.log('Error logging achievement_list')
                self.log(json.loads(res))
        if isIn('unit_info', res) and not isIn('BattleArenaStart', res):
            if str(self.wizard_id) in str(res):
                try:
                    self._update_unit_list(json.loads(res)['unit_info'])
                    self._parseUnitListRunes([json.loads(res)['unit_info']])
                    self.log(self._getUnitList())
                except KeyError:
                    self.log('Error logging unit_info')
                    self.log(json.loads(res))
        if isIn('arena_list', res):
            try:
                self._updateArenaList(json.loads(res)['arena_list'])
                self.log(self._getArenaList())
            except KeyError:
                self.log('Error logging arena_list')
                self.log(json.loads(res))
        if isIn('arena_log', res):
            try:
                self._updateArenaLog(json.loads(res)['arena_log'])
                self.log(self._getArenaLog())
            except KeyError:
                self.log('Error logging arena_log')
                self.log(json.loads(res))
        if isIn('building_list', res):
            try:
                self._updateBuildings(json.loads(res)['building_list'])
                self.log(self._getBuildings())
            except KeyError:
                self.log('Error logging building_list')
                self.log(json.loads(res))
        if isIn('market_list', res):
            try:
                self._updateMarketList(json.loads(res)['market_list'])
                self.log(self._getMarketList())
            except KeyError:
                self.log('Error logging market_list')
                self.log(json.loads(res))
        if isIn('unit_depository_slots', res):
            try:
                self._updateUnitDepositorySlots(json.loads(res)['unit_depository_slots'])
                self.log(self._getUnitDepositorySlots())
            except KeyError:
                self.log('Error logging unit_depository_slots')
                self.log(json.loads(res))
        if isIn('market_info', res):
            try:
                self._updateMarketInfo(json.loads(res)['market_info'])
                self.log(self._getMarketInfo())
            except KeyError:
                self.log('Error logging market_info')
                self.log(json.loads(res))
        if isIn('mail_list', res):
            try:
                self._updateMailList(json.loads(res)['mail_list'])
                self.log(self._getMailList())
            except KeyError:
                self.log('Error logging mail_list')
                self.log(json.loads(res))
        if isIn('wish_info', res):
            try:
                self._updateWishInfo(json.loads(res)['wish_info'])
                self.log(self._getWishInfo())
            except KeyError:
                self.log('Error logging wish_info')
                self.log(json.loads(res))
        if isIn('scenario_list', res):
            try:
                self._update_scenario_list(json.loads(res)['scenario_list'])
                self.log(self._getScenarioList())
            except KeyError:
                self.log('Error logging scenario_list')
                self.log(json.loads(res))
        if isIn('dungeon_list', res) and not isIn('GetEventTimeTable', res):
            try:
                self._update_dungeon_list(json.loads(res)['dungeon_list'])
                self.log(self._getDungeonList())
            except KeyError:
                self.log('Error logging dungeon_list')
                self.log(json.loads(res))
        if isIn('unit_list', res):
            try:
                self._update_unit_list(json.loads(res)['unit_list'])
                self.log(self._getUnitList())
            except KeyError:
                self.log('Error logging unit_list')
                self.log(json.loads(res))
        if isIn('rune', res):
            try:
                self._updateRune(json.loads(res)['reward']['crate']['rune'])
                self.log(self._getRuneList())
            except KeyError:
                try:
                    self._updateRune(json.loads(res)['rune'])
                    self.log(self._getRuneList())
                except KeyError:
                    self.log('Error logging rune')
                    self.log(json.loads(res))
        if isIn('inventory_info', res):
            try:
                self._updateInventoryList(json.loads(res)['inventory_info'])
                self.log(self._getInventoryList())
            except KeyError:
                self.log('Error logging inventory_info')
                self.log(json.loads(res))
        if isIn('quest_info', res):
            try:
                self._updateDailyQuestList([json.loads(res)['quest_info']])
                self.log(self._getDailyQuestList())
            except KeyError:
                self.log('Error logging quest_info')
                self.log(json.loads(res))
        if isIn('quest_list', res):
            try:
                self._updateDailyQuestList(json.loads(res)['quest_list'])
                self.log(self._getDailyQuestList())
            except KeyError:
                self.log('Error logging quest_list')
                self.log(json.loads(res))
        if isIn('friend_list', res):
            try:
                self._updateFriendList(json.loads(res)['friend_list'])
                self.log(self._getFriendList())
            except KeyError:
                self.log('Error logging friend_list')
                self.log(json.loads(res))
        if isIn('helper_list', res):
            try:
                self._updateHelperList(json.loads(res)['helper_list'])
                self.log('Helpers: {}'.format(self._getHelperList()))
            except KeyError:
                self.log('Error logging helper_list')
                self.log(json.loads(res))
        if isIn('gifted_list', res):
            try:
                self._updateGiftedFriends(json.loads(res)['gifted_list'])
                self.log(self._getFriendList())
            except KeyError:
                self.log('Error logging gifted_list')
                self.log(json.loads(res))
        if isIn('harvest_mana', res):
            try:
                self.log('Harvested {} mana from building {}'.format(json.loads(res)['harvest_mana'],
                                                                     json.loads(res)['building_info']['building_id']))
            except KeyError:
                self.log('Error logging harvest_mana')
                self.log(json.loads(res))
        if isIn('harvest_crystal', res):
            try:
                self.log('Harvested {} crystal from building {}'.format(json.loads(res)['harvest_crystal'],
                                                                        json.loads(res)['building_info'][
                                                                            'building_id']))
            except KeyError:
                self.log('Error logging harvest_crystal')
                self.log(json.loads(res))
        if isIn('daily_reward_info', res):
            try:
                self._update_daily_reward_info(json.loads(res)['daily_reward_info'])
                self.log(self._getDailyRewardInfo())
            except KeyError:
                self.log('Error logging daily_reward_info')
                self.log(json.loads(res))
        if isIn('pvp_info', res):
            try:
                self._updatePvpInfo(json.loads(res)['pvp_info'])
                self.log(self._getPvpInfo())
            except KeyError:
                self.log('Error logging pvp_info')
                self.log(json.loads(res))

    def _check_ret_code(self, res, rj):
        if isIn('ret_code', res):
            if rj['ret_code'] != 0:
                self.log('failed to send data for {}'.format(rj['command']))
                self.log('ret_code: {}'.format(rj['ret_code']))
                self.log('')
                return None
            self.log('ret_code: {} command: {}'.format(rj['ret_code'], rj['command']))
        return rj

    def _check_request_data(self, data):
        if isIn('UpgradeUnit', data) or isIn('SacrificeUnit', data):
            try:
                self._remove_unit(json.loads(data)['source_list'])
                self.log(self._getUnitList())
            except KeyError:
                self.log('Error removing unit sacrifized or used for upgrade.')
                self.log(json.loads(data))
        if isIn('rune_id_list', data):
            try:
                self._removeRune(json.loads(data)['rune_id_list'])
                self.log(self._getRuneList())
            except KeyError:
                self.log('Error removing rune')
                self.log(json.loads(data))

    def level8(self):
        self.UpdateEventStatus(501)
        self.UpdateEventStatus(502)
        self.UpdateEventStatus(503)
        self.UpdateEventStatus(504)
        self.UpdateEventStatus(530)
        self.UpdateEventStatus(3)
        self.UpdateEventStatus(505)
        self.UpdateEventStatus(5)
        self.UpdateEventStatus(60018)
        self.UpdateEventStatus(80001)
        self.UpdateEventStatus(4)
        self.UpdateEventStatus(10001)
        self.UpdateEventStatus(508)
        self.UpdateEventStatus(507)
        self.UpdateEventStatus(506)
        self.UpdateEventStatus(509)
        self.UpdateEventStatus(510)
        self.UpdateEventStatus(531)
        self.UpdateEventStatus(6)
        self.UpdateEventStatus(511)
        self.UpdateEventStatus(60005)
        self.UpdateEventStatus(17)
        self.UpdateEventStatus(50007)
        self.UpdateEventStatus(540)
        self.UpdateEventStatus(541)
        self.UpdateEventStatus(542)
        self.UpdateEventStatus(543)
        self.UpdateEventStatus(544)
        self.UpdateEventStatus(545)
        self.UpdateEventStatus(18)
        self.UpdateEventStatus(546)
        self.UpdateEventStatus(8)
        self.UpdateEventStatus(20001)
        self.UpdateEventStatus(513)
        self.UpdateEventStatus(512)
        self.UpdateEventStatus(514)
        self.UpdateEventStatus(515)
        self.UpdateEventStatus(516)
        self.UpdateEventStatus(532)
        self.UpdateEventStatus(9)
        self.UpdateEventStatus(517)
        self.UpdateEventStatus(10)
        self.UpdateEventStatus(519)
        self.UpdateEventStatus(518)
        self.UpdateEventStatus(520)
        self.UpdateEventStatus(521)
        self.UpdateEventStatus(522)
        self.UpdateEventStatus(533)
        self.UpdateEventStatus(523)
        self.UpdateEventStatus(12)
        self.UpdateEventStatus(13)
        self.UpdateEventStatus(19)
        self.UpdateEventStatus(1008)
        self.UpdateEventStatus(1010)
        self.UpdateEventStatus(547)
        self.UpdateEventStatus(548)
        self.UpdateEventStatus(549)
        self.UpdateEventStatus(550)
        self.UpdateEventStatus(551)
        self.UpdateEventStatus(552)
        self.UpdateEventStatus(20)
        self.UpdateEventStatus(553)
        self.UpdateEventStatus(21)
        self.UpdateEventStatus(14)
        self.UpdateEventStatus(50029)
        self.UpdateEventStatus(524)
        self.UpdateEventStatus(525)
        self.UpdateEventStatus(526)
        self.UpdateEventStatus(527)
        self.UpdateEventStatus(528)
        self.UpdateEventStatus(529)
        self.UpdateEventStatus(534)
        self.UpdateEventStatus(15)
        self.UpdateEventStatus(70001)
        self.UpdateEventStatus(70005)
        self.UpdateEventStatus(22)
        self.UpdateEventStatus(554)
        self.UpdateEventStatus(555)
        self.UpdateEventStatus(556)
        self.UpdateEventStatus(557)
        self.UpdateEventStatus(558)
        self.UpdateEventStatus(559)
        self.UpdateEventStatus(23)
        self.UpdateEventStatus(560)
        self.UpdateEventStatus(24)
        self.UpdateEventStatus(1020)
        self.UpdateEventStatus(562)
        self.UpdateEventStatus(561)
        self.UpdateEventStatus(563)
        self.UpdateEventStatus(564)
        self.UpdateEventStatus(565)
        self.UpdateEventStatus(566)
        self.UpdateEventStatus(567)
        self.UpdateEventStatus(25)
        self.UpdateEventStatus(26)
        self.UpdateEventStatus(27)
        self.UpdateEventStatus(1030)
        self.UpdateEventStatus(568)
        self.UpdateEventStatus(569)
        self.UpdateEventStatus(570)
        self.UpdateEventStatus(571)
        self.UpdateEventStatus(572)
        self.UpdateEventStatus(573)
        self.UpdateEventStatus(574)
        self.UpdateEventStatus(28)
        self.UpdateEventStatus(29)
        self.UpdateEventStatus(575)
        self.UpdateEventStatus(576)
        self.UpdateEventStatus(577)
        self.UpdateEventStatus(578)
        self.UpdateEventStatus(579)
        self.UpdateEventStatus(580)
        self.UpdateEventStatus(581)
        self.UpdateEventStatus(30)
        self.UpdateEventStatus(31)
        self.UpdateEventStatus(582)
        self.UpdateEventStatus(583)
        self.UpdateEventStatus(584)
        self.UpdateEventStatus(586)
        self.UpdateEventStatus(585)
        self.UpdateEventStatus(587)
        self.UpdateEventStatus(588)
        self.UpdateEventStatus(32)
        self.UpdateEventStatus(60006)
        self.UpdateEventStatus(60025)
        self.UpdateEventStatus(33)
        self.UpdateEventStatus(589)
        self.UpdateEventStatus(590)
        self.UpdateEventStatus(591)
        self.UpdateEventStatus(592)
        self.UpdateEventStatus(593)
        self.UpdateEventStatus(594)
        self.UpdateEventStatus(595)
        self.UpdateEventStatus(34)
        self.UpdateEventStatus(34)
        self.UpdateEventStatus(35)
        self.UpdateEventStatus(36)
        self.UpdateEventStatus(50038)
        self.UpdateEventStatus(10017)
        self.UpdateEventStatus(10019)
        self.UpdateEventStatus(1033)
        self.UpdateEventStatus(50025)
        self.UpdateEventStatus(1026)
