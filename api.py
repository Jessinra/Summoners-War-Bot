from collections import OrderedDict
from crypt import Crypter
from qpyou import QPYOU
from tools import Tools
import json
import requests
import sys
import time
import socket
import math

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class API(object):
	def __init__(self,uid,did,id=None,email=None,session=None):
		self.crypter=Crypter()
		self.s=requests.session()
		self.s.verify=False
		self.s.headers.update({'User-Agent':'SMON_Kr/3.7.9.37900 CFNetwork/808.2.16 Darwin/16.3.0'})
		if 'Admin-PC' == socket.gethostname():
			self.s.proxies.update({'http': 'http://127.0.0.1:8888','https': 'https://127.0.0.1:8888',})
		self.game_index=2623
		self.proto_ver=11060
		self.app_version='3.7.9'
		self.c2_api='http://summonerswar-%s.qpyou.cn/api/gateway_c2.php'
		self.uid=int(uid)
		self.did=int(did)
		self.isHive=False
		self.ts_val = 0
		self.session_start = math.ceil(time.time())
		if id and email:
			self.log('hive account')
			self.id=id
			self.email=email
			self.isHive=True
			self.session_key=session
		self.log('uid:%s did:%s'%(uid,did))

	def setRegion(self,region):
		regions=['gb','hub','jp','cn','sea','eu']
		'''
		gb = global
		eu = europe
		jp = japan
		sea = asia
		cn = china
		hub = ?
		'''
		if region not in regions:
			self.log('invalid region, choose one from these:%s'%(','.join(regions)))
			exit(1)
		self.region=region
		self.c2_api=self.c2_api%(self.region)
		
	def setIDFA(self,id):
		self.idfa=id
		
	def log(self,msg):
		print '[%s]:%s'%(time.strftime('%H:%M:%S'),msg)
		
	def callAPI(self,path,data):
		if type(data)<>str:
			data=json.dumps(data).replace(' ','')
		data=self.crypter.encrypt_request(data,2 if '_c2.php' in path else 1)
		res=self.s.post(path,data)
		res= self.crypter.decrypt_response(res.content,2 if '_c2.php' in path else 1)
		if 'wizard_info' in res and 'wizard_id' in res:
			self.updateWizard(json.loads(res)['wizard_info'])
		if '\'ts_val\'' in res or '\"ts_val\"' in res:
			try:
				self._update_ts_val(json.loads(res)['ts_val])
			except KeyError:
				self.log('Error logging ts_val')
				self.log(json.loads(res))
		rj=json.loads(res)
		if 'ret_code' in res:
			if rj['ret_code']<>0:
				self.log('failed to send data for %s'%(rj['command']))
				return None
			self.log('ret_code:%s command:%s'%(rj['ret_code'],rj['command']))
		return rj

	def getServerStatus(self):
		data={}
		data['game_index']=self.game_index
		data['proto_ver']=self.proto_ver
		data['channel_uid']=0
		return self.callAPI('http://summonerswar-eu.qpyou.cn/api/server_status_c2.php',data)

	def getVersionInfo(self):
		data={}
		data['game_index']=self.game_index
		data['proto_ver']=self.proto_ver
		data['channel_uid']=0
		res= self.callAPI('http://summonerswar-eu.qpyou.cn/api/version_info_c2.php',data)
		self.parseVersionData(res['version_data'])
		return res
		
	def parseVersionData(self,input):
		for v in input:
			if v['topic']=='protocol':
				self.log('found proto_ver:%s'%(v['version']))
				self.proto_ver=int(v['version'])
			if v['topic']=='infocsv':
				self.log('found infocsv:%s'%(v['version']))
				self.infocsv=v['version']
	
	def base_data(self,cmd,kind=1):
		ts_val = self.ts_val + math.ceil(time.time()) - self.session_start
		if kind == 1:
			data=OrderedDict([('command',cmd),('game_index',self.game_index),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid)])
		elif kind ==2:
			data=OrderedDict([('command',cmd),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.uid),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val', ts_val)])
		return data

	def CheckLoginBlock(self):
		data=self.base_data('CheckLoginBlock')
		return self.callAPI(self.c2_api,data)

	def GetDailyQuests(self):
		data=self.base_data('GetDailyQuests',2)
		return self.callAPI(self.c2_api,data)

	def GetMiscReward(self):
		data=self.base_data('GetMiscReward',2)
		return self.callAPI(self.c2_api,data)

	def GetMailList(self):
		data=self.base_data('GetMailList',2)
		return self.callAPI(self.c2_api,data)

	def GetArenaLog(self):
		data=self.base_data('GetArenaLog',2)
		return self.callAPI(self.c2_api,data)

	def ReceiveDailyRewardSpecial(self):
		data=self.base_data('ReceiveDailyRewardSpecial',2)
		return self.callAPI(self.c2_api,data)

	def GetFriendRequest(self):
		data=self.base_data('GetFriendRequest',2)
		return self.callAPI(self.c2_api,data)

	def GetChatServerInfo(self):
		data=self.base_data('GetChatServerInfo',2)
		return self.callAPI(self.c2_api,data)

	def getRtpvpRejoinInfo(self):
		data=self.base_data('getRtpvpRejoinInfo',2)
		return self.callAPI(self.c2_api,data)

	def GetNoticeDungeon(self):
		data=self.base_data('GetNoticeDungeon',2)
		return self.callAPI(self.c2_api,data)

	def GetNoticeChat(self):
		data=self.base_data('GetNoticeChat',2)
		return self.callAPI(self.c2_api,data)

	def GetNpcFriendList(self):
		data=self.base_data('GetNpcFriendList',2)
		return self.callAPI(self.c2_api,data)

	def GetWizardInfo(self):
		data=self.base_data('GetWizardInfo',2)
		return self.callAPI(self.c2_api,data)

	def CheckDailyReward(self):
		data=self.base_data('CheckDailyReward',2)
		return self.callAPI(self.c2_api,data)

	def gettrialtowerupdateremained(self):
		data=self.base_data('gettrialtowerupdateremained',2)
		return self.callAPI(self.c2_api,data)

	def SetWizardName(self,name):
		self.log('new name:%s'%(name))
		data=OrderedDict([('command','SetWizardName'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454178'),('wizard_name',name)])
		return self.callAPI(self.c2_api,data)

	def UpdateEventStatus(self,event_id):
		data=OrderedDict([('command','UpdateEventStatus'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454202'),('event_id',event_id)])
		return self.callAPI(self.c2_api,data)

	def GetEventTimeTable(self):
		data=OrderedDict([('command','GetEventTimeTable'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454203'),('lang','1'),('app_version',self.app_version)])
		return self.callAPI(self.c2_api,data)

	def Harvest(self,building_id):
		self.log('harvesting from:%s'%(building_id))
		data=OrderedDict([('command','Harvest'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454214'),('building_id',building_id)])
		return self.callAPI(self.c2_api,data)

	def TriggerShopItem(self,trigger_id):
		data=OrderedDict([('command','TriggerShopItem'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454226'),('trigger_id',trigger_id)])
		return self.callAPI(self.c2_api,data)

	def UpdateAchievement(self,ach_list):
		data=OrderedDict([('command','UpdateAchievement'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454226'),('ach_list',ach_list)])
		return self.callAPI(self.c2_api,data)

	def UpdateDailyQuest(self,quests):
		data=OrderedDict([('command','UpdateDailyQuest'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454226'),('quests',quests)])
		return self.callAPI(self.c2_api,data)

	def getUID(self):
		if self.isHive:
			return self.session_key
		else:
			return self.uid
		
	def BattleScenarioStart(self,region_id,stage_no,difficulty,unit_id_list):
		data=OrderedDict([('command','BattleScenarioStart'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454271'),('region_id',region_id),('stage_no',stage_no),('difficulty',difficulty),('unit_id_list',unit_id_list),('helper_list','[]'),('mentor_helper_list','[]'),('npc_friend_helper_list','[]'),('retry','0')])
		return self.callAPI(self.c2_api,data)

	def BattleScenarioResult(self,battle_key,opp_unit_status_list,unit_id_list,position):
		data=OrderedDict([('command','BattleScenarioResult'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454039'),('battle_key',battle_key),('win_lose','1'),('opp_unit_status_list',opp_unit_status_list),('unit_id_list',unit_id_list),('position',position),('clear_time','34524'),('retry','0')])
		return self.callAPI(self.c2_api,data)

	def SummonUnit(self,building_id,mode,pos_arr):
		data=OrderedDict([('command','SummonUnit'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454069'),('building_id',building_id),('mode',mode),('pos_arr',pos_arr)])
		return self.callAPI(self.c2_api,data)

	def EquipRune(self,rune_id,unit_id):
		data=OrderedDict([('command','EquipRune'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454084'),('rune_id',rune_id),('unit_id',unit_id)])
		return self.callAPI(self.c2_api,data)

	def UpgradeRune(self,rune_id,upgrade_curr,cash_used,stone_used):
		data=OrderedDict([('command','UpgradeRune'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454107'),('rune_id',rune_id),('upgrade_curr',upgrade_curr),('cash_used',cash_used),('stone_used',stone_used)])
		return self.callAPI(self.c2_api,data)

	def BuyShopItem(self,item_id,island_id,pos_x,pos_y):
		data=OrderedDict([('command','BuyShopItem'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454125'),('item_id',item_id),('island_id',island_id),('pos_x',pos_x),('pos_y',pos_y)])
		return self.callAPI(self.c2_api,data)

	def ClaimAchievementReward(self,ach_id):
		data=OrderedDict([('command','ClaimAchievementReward'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454428'),('ach_id',ach_id)])
		return self.callAPI(self.c2_api,data)

	def SacrificeUnit(self,target_id,source_list):
		data=OrderedDict([('command','SacrificeUnit'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178454138'),('target_id',target_id),('island_id','1'),('building_id','0'),('pos_x','8'),('pos_y','14'),('source_list',source_list)])
		return self.callAPI(self.c2_api,data)

	def ReceiveMail(self,mail_id_list):
		data=OrderedDict([('command','ReceiveMail'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178264258'),('mail_id_list',mail_id_list),('island_id','1'),('pos_x','19'),('pos_y','27')])
		return self.callAPI(self.c2_api,data)

	def GetWorldBossStatus(self,worldboss_id):
		data=OrderedDict([('command','GetWorldBossStatus'),('wizard_id',self.wizard_id),('session_key',self.getUID()),('proto_ver',self.proto_ver),('infocsv',self.infocsv),('channel_uid',self.uid),('ts_val','1178264277'),('wizard_id',self.wizard_id),('worldboss_id',worldboss_id)])
		return self.callAPI(self.c2_api,data)

	def setUser(self,input):
		self.user=input
		self.wizard_id=input['wizard_info']['wizard_id']
		self.log('wizard_id:%s'%(self.wizard_id))
	
	def updateWizard(self,input):
		if hasattr(self, 'user'):
			self.user['wizard_info']=input
			self.log(self.getUserInfo())
							    
	def _update_ts_val(self, input_):
		self.ts_val = input_
		self.session_start = math.ceil(time.time())
	
	def getUserInfo(self):
		return 'id:%s username:%s energy:%s mana:%s crystal:%s'%(self.user['wizard_info']['wizard_id'],self.user['wizard_info']['wizard_name'],self.user['wizard_info']['wizard_energy'],self.user['wizard_info']['wizard_mana'],self.user['wizard_info']['wizard_crystal'])
		
	def GuestLogin(self):
		data=OrderedDict([('command','GuestLogin'),('game_index',self.game_index),('proto_ver',self.proto_ver),('app_version',self.app_version),('infocsv',self.infocsv),('uid',self.uid),('channel_uid',self.uid),('did',self.did),('push',1),('is_emulator',0),('country','DE'),('lang','eng'),('lang_game',1),('mac_address','02:00:00:00:00:00'),('device_name','iPhone10,6'),('os_version','11.1'),('token','0000000000000000000000000000000000000000000000000000000000000000'),('idfv',self.idfa),('adid','00000000-0000-0000-0000-000000000000'),('binary_size',10448304),('binary_check','87c2986b797cfdf61e5816809395ad8d'),('create_if_not_exist',1)])
		res= self.callAPI(self.c2_api,data)
		self.setUser(res)
		self.log(self.getUserInfo())
		return res	

	def login(self):
		if self.isHive:
			return self.HubUserLogin()
		else:
			return self.GuestLogin()
		
	def HubUserLogin(self):
		data=OrderedDict([('command','HubUserLogin'),('game_index',self.game_index),('proto_ver',self.proto_ver),('app_version',self.app_version),('session_key',self.session_key),('infocsv',self.infocsv),('uid',self.uid),('channel_uid',self.uid),('did',self.did),('id',self.id),('email',self.email),('push',1),('is_emulator',0),('country','RU'),('lang','eng'),('lang_game',1),('mac_address','02:00:00:00:00:00'),('device_name','iPhone10,6'),('os_version','11.1'),('token','0000000000000000000000000000000000000000000000000000000000000000'),('idfv',self.idfa),('adid','00000000-0000-0000-0000-000000000000'),('binary_size',10347504),('binary_check','438656fa18e8d547df1393060cc6be53'),('create_if_not_exist',0)])
		res= self.callAPI(self.c2_api,data)
		self.setUser(res)
		self.log(self.getUserInfo())
		return res
		
	def parseBattleStart(self,input):
		battle_key=input['battle_key']
		opp_unit_status_list=[]
		for i in input['opp_unit_list'][0]:
			opp_unit_status_list.append({'unit_id':i['unit_id'],'result':2})
		return battle_key,opp_unit_status_list
		
	def parseBattleResult(self,input):
		self.log('quest finished, win:%s'%(input['win_lose']))
		self.log('rewards:%s'%(input['reward']))
		
	def doMission(self,region_id,stage_no,difficulty):
		unit_id_list=[]
		for unit in self.user['defense_unit_list']:
			unit_id_list.append({'unit_id':unit['unit_id']})
		battle_start=self.BattleScenarioStart(region_id,stage_no,difficulty,unit_id_list)
		if not battle_start:
			self.log('dont have battle data')
			return
		res=self.parseBattleStart(battle_start)
		battle_end=self.BattleScenarioResult(res[0],res[1],self.user['defense_unit_list'],{"island_id":1,"pos_x":14,"pos_y":24})
		self.parseBattleResult(battle_end)

	def completeTutorial(self):
		self.getServerStatus()
		self.getVersionInfo()
		
		self.CheckLoginBlock()
		self.login()
		self.GetDailyQuests()
		self.GetMiscReward()
		self.GetMailList()#4
		self.GetArenaLog()#5
		self.ReceiveDailyRewardSpecial()
		self.GetFriendRequest()
		self.GetChatServerInfo()
		self.getRtpvpRejoinInfo()
		self.SetWizardName((Tools().rndHex(9)))#10
		self.UpdateEventStatus(1500)
		self.GetEventTimeTable()
		self.GetNoticeDungeon()
		self.GetNoticeChat()
		for building in self.user['building_list']:
			if 'harvest_max' in building:
				building_id=building['building_id']
		self.Harvest(building_id)#15
		self.UpdateEventStatus(60021)
		self.UpdateEventStatus(1085)
		self.TriggerShopItem(20)#18
		for building in self.user['building_list']:
			if building['building_master_id'] ==2:
				building_id=building['building_id']
		second_unit=self.SummonUnit(building_id,1,[{"island_id":1,"pos_x":7,"pos_y":7,"unit_master_id":10602}])#19
		second_unit=second_unit['unit_list'][0]['unit_id']
		self.UpdateEventStatus(1501)
		self.UpdateAchievement([{"ach_id":2,"cond_id":2,"current":1}])
		self.UpdateAchievement([{"ach_id":15,"cond_id":2,"current":1}])
		defense_unit_list=self.SummonUnit(building_id,3,[{"island_id":1,"pos_x":27,"pos_y":18,"unit_master_id":10101}])#23
		self.UpdateAchievement([{"ach_id":2,"cond_id":1,"current":1},{"ach_id":15,"cond_id":1,"current":1},{"ach_id":33,"cond_id":1,"current":1}])
		self.UpdateDailyQuest([{"quest_id":3,"progressed":1}])
		self.UpdateEventStatus(1502)
		unit_id_list=[]
		first_unit=defense_unit_list['unit_list'][0]['unit_id']
		for unit in defense_unit_list['defense_unit_list']:
			unit_id_list.append({'unit_id':unit['unit_id']})
		unit_id_list.sort()
		battle_start=self.BattleScenarioStart(1,1,1,unit_id_list)#27
		res=self.parseBattleStart(battle_start)
		self.UpdateDailyQuest([{"quest_id":1,"progressed":3}])#28
		self.UpdateEventStatus(50001)
		self.UpdateAchievement([{"ach_id":3,"cond_id":1,"current":1}])
		self.UpdateAchievement([{"ach_id":3,"cond_id":2,"current":1}])
		self.UpdateEventStatus(50035)
		unit_id_list=[]
		pos=0
		for unit in defense_unit_list['defense_unit_list']:
			unit_id_list.append({'unit_id':unit['unit_id'],'pos_id':pos})
			pos+=1
		battle_end=self.BattleScenarioResult(res[0],res[1],unit_id_list,{"island_id":1,"pos_x":14,"pos_y":24})
		self.parseBattleResult(battle_end)
		self.UpdateEventStatus(1503)
		self.UpdateEventStatus(1504)
		self.GetEventTimeTable()#36
		self.SummonUnit(building_id,1,[{"island_id":1,"pos_x":27,"pos_y":18,"unit_master_id":15203}])#37
		self.UpdateAchievement([{"ach_id":2,"cond_id":3,"current":1},{"ach_id":15,"cond_id":3,"current":1}])
		self.UpdateDailyQuest([{"quest_id":3,"progressed":2}])
		self.UpdateEventStatus(1506)
		self.UpdateEventStatus(1507)#41
		for rune in self.user['runes']:
			rune_id=rune['rune_id']
		self.EquipRune(rune_id,first_unit)
		self.UpgradeRune(rune_id,0,0,0)
		self.UpdateDailyQuest([{"quest_id":4,"progressed":1}])
		self.BuyShopItem('800020',1,21,20)#45
		self.UpdateEventStatus(1508)
		self.UpdateEventStatus(1509)
		self.SacrificeUnit(second_unit,[{"source_id":0}])
		self.UpdateAchievement([{"ach_id":13,"cond_id":1,"current":1}])
		self.UpdateAchievement([{"ach_id":31,"cond_id":1,"current":1}])
		self.UpdateDailyQuest([{"quest_id":2,"progressed":1}])
		self.UpdateEventStatus(1510)
		self.UpdateAchievement([{"ach_id":1,"cond_id":1,"current":1}])
		self.UpdateEventStatus(2)
		self.UpdateAchievement([{"ach_id":6,"cond_id":1,"current":1},{"ach_id":6,"cond_id":2,"current":1},{"ach_id":6,"cond_id":3,"current":1}])
		self.UpdateAchievement([{"ach_id":263,"cond_id":1,"current":1}])

if __name__ == "__main__":
	uid,did=QPYOU().createNew()
	a=API(uid,did)
	a.setIDFA(Tools().rndDeviceId())
	a.completeTutorial()
	#a.getServerStatus()
	#a.getVersionInfo()
	#a.CheckLoginBlock()
	#a.login()
