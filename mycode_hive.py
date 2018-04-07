from api import API
from qpyou import QPYOU
from tools import rndDeviceId
import json
import random

my_email=''
my_hivelogin=''
my_password=''
# Leave empty if you don't know device id
device_id = ''
device = ''

try:
    data = None
    with open('config.json', 'r') as f:
        data = json.load(f)
        if data.get('device_id'):
            device_id = data.get('device_id')
        else:
            device_id = str(random.randint(200000000, 300000000))
            data.update({'device_id': device_id})
    with open('config.json', 'w') as f:
        f.write(json.dumps(data))
except FileNotFoundError:
    with open('config.json', 'w') as f:
        device_id = str(random.randint(200000000, 300000000))
        data = {
            'device_id': device_id
        }
        f.write(json.dumps(data))

uid,did,sessionkey,appId=QPYOU(device_id, device).hiveLogin(my_hivelogin,my_password)
a=API(uid,did,my_hivelogin,my_email,sessionkey,device=device,app_id=appId)
a.set_region('eu')
a.set_idfa(rndDeviceId())
a.getLocation()
a.getServerStatus()
a.getVersionInfo()
a.CheckLoginBlock()
a.login()
a.GetDailyQuests()
a.GetMiscReward()
a.GetMailList()
a.CheckDailyReward()
a.GetArenaLog()
a.CheckDarkPortalStatus()
a.GetCostumeCollectionList()
a.ReceiveDailyRewardSpecial()
a.receiveDailyRewardInactive()
a.GetFriendRequest()
a.getUnitUpgradeRewardInfo()
a.GetRTPvPInfo_v3()
a.GetChatServerInfo()
a.getRtpvpRejoinInfo()
a.GetEventTimeTable()
a.GetNoticeChat()
a.GetNoticeDungeon()
a.GetDungeonList()
a.GetInstanceList()
a.gettrialtowerupdateremained()
a.GetTrialTowerInfo_v2()

# add your things afterwards


#a.doMission(1,1,1)#garen forest outskirts
#a.doMission(1,2,1)#garen forest south
#a.doMission(1,3,1)#garen forest east
#a.doMission(1,4,1)#garen forest paths
