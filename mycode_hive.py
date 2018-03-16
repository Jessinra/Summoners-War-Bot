from api import API
from qpyou import QPYOU
from tools import rndDeviceId

my_email='s@mila432.com'
my_hivelogin='mila432f'
my_password='hallo123'

uid,did,sessionkey,appId=QPYOU('236145028').hiveLogin(my_hivelogin,my_password)
a=API(uid,did,my_hivelogin,my_email,sessionkey,device=None,app_id=appId)
a.setRegion('eu')
a.setIDFA(rndDeviceId())
a.getServerStatus()
a.getVersionInfo()
a.CheckLoginBlock()
a.login()
a.doMission(1,1,1)#garen forest outskirts
a.doMission(1,2,1)#garen forest south
a.doMission(1,3,1)#garen forest east
a.doMission(1,4,1)#garen forest paths
