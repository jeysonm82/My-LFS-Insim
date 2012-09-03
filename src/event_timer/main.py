'''
Created on Feb 5, 2012
EVENT TIMER
Displays a button message to everyone in the server with a regressive counter
@author: jason_new

'''
from evt import EVT
import pyinsim
a=EVT()
a.traker_enabled=False
a.connect()
a.run(True)
