'''
Created on Nov 17, 2011
Pit warning. Para Nascart (LFSCOL). TODO borrar
@author: jason_new
'''
from pwarn import PitInformant

a=PitInformant()
a.init_tracker()
a.connect()
a.draw_pbut()
a.run(True)
