'''
Created on Feb 16, 2012

@author: jason_new
'''
from exp import Example_Insim

a=Example_Insim()
a.init_tracker()#initialize tracker
a.connect()
a.do_stuff()
a.run(True)