from api import API
from qpyou import QPYOU
from tools import rndDeviceId

my_email=''
my_hivelogin=''
my_password=''
# Leave empty if you don't know device id
device_id = ''
device = ''

uid,did,sessionkey,appId=QPYOU(device_id, device).hiveLogin(my_hivelogin,my_password)
a=API(uid,did,my_hivelogin,my_email,sessionkey,device=device,app_id=appId)
a.set_region('eu')
a.set_idfa(rndDeviceId())
a.getLocation()
a.getServerStatus()
a.getVersionInfo()
a.CheckLoginBlock()
a.login()
#a.doMission(1,1,1)#garen forest outskirts
#a.doMission(1,2,1)#garen forest south
#a.doMission(1,3,1)#garen forest east
#a.doMission(1,4,1)#garen forest paths
