'''
Created on Feb 16, 2012

@author: jason_new
'''
from myinsim.insim_client import InsimClient, WorkDaemon
import pyinsim
import random
class Example_Insim(InsimClient):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        InsimClient.__init__(self, tag="Example_Insim")
        self.version=0.1
        self.flags=pyinsim.ISF_CON|pyinsim.ISF_OBH #connection flags
        
        #read a config.cfg parameter
        self.config_par=self.config.get("section","foo")
        print self.config_par
        
    def do_stuff(self):
        #send a message
        self.sendMsg("^3 Hello world. message")
        #send a chat
        self.sendMsg("^7 Hello world. chat", '')
        
        #creates a button
        self.send_button(1, 100, 100, 30, 15, "^7 Message", 255, pyinsim.ISB_DARK)
        
        #create a thread daemon that runs a process each [interval] seconds
        j=WorkDaemon(work_method=self.work_method, interval=1)
        j.start()
    
    def work_method(self):
        print "Calling work method"
        t=str(random.randint(100,999))
        self.send_button(2, 130, 140, 30, 15, "^"+t, 255, pyinsim.ISB_DARK)
        
    def split_time(self, insim, split):
        '''
         Overwrite InsimCLient split_time that is binded to the SPLIT TIME packet
        '''
        #always call original method first
        InsimClient.split_time(self, insim, split)
        
        print "Split time received. "
        self.sendMsg("Split time from "+self.get_driver(split.PLID).playername)
    
    def hidden_message(self, insim, msg):
        '''
        admin messages sent with /i
        '''
        InsimClient.hidden_message(self, insim, msg)
        self.sendChat("Hidden message: "+msg.Msg)
        