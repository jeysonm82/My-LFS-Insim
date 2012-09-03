'''
Created on Nov 3, 2011
Crash List
Keep track of contacts. Can store contacts in a file too.
@author: jason_new
'''
from myinsim.insim_client import InsimClient
from crash_list.c_list import Crash_List

import time


a=Crash_List()
#a.traker_enabled=True
#a.init_tracker()
a.connect()

a.init_tracker()
#a.sendButton(140, 100, 30, 20, 'Mensage de prueba')
a.begin()
a.get_track_name()

a.run(False)

