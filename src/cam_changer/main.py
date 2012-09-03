'''
Created on Feb 14, 2012
Camera changer
Simple camera changer (default and custom cameras). Run locally
@author: jason_new
'''
from camsim import Cam_Sim

a=Cam_Sim()
a.init_tracker()
a.connect()
a.run(True)