'''
Created on Dec 11, 2011

@author: jason_new
'''
from myinsim.insim_client import InsimClient,WorkDaemon
import pyinsim
class TestInsim(InsimClient):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        InsimClient.__init__(self, 'TESTINSIM')
        self.flags=pyinsim.ISF_HLV| pyinsim.ISF_CON | pyinsim.ISF_OBH
        self.sa=self.config.get("test","showall")
    def new_player(self,insim, npl):
        InsimClient.new_player(self, insim, npl)
        print 'Player ', npl.PName, ' FLAGS ', self.dec2listbin(npl.Flags), ' LEN : ',len(self.dec2listbin(npl.Flags))
        
    def lap_time(self,insim,lap):
        InsimClient.lap_time(self, insim, lap)
        #print 'Player ', self.drivers[self.driversID[lap.PLID]].playername, ' FLAGS ', self.dec2listbin(lap.Flags), ' LEN : ',len(self.dec2listbin(lap.Flags))
        
    def hlv(self,insim, p):
        InsimClient.hlv(self, insim, p)
        #print p
        reason={1:'Contact with Wall/Car/Obj',0:'Ground',4:'Speeding'}
        #self.sendMsg('^1HLV PACKET:^7 '+reason[p.HLVC]+' Sp: '+str(p.C.Speed)+ ' H: '+str(p.C.Heading)+ ' D: '+str(p.C.Direction) ,'')
        b=False
        if("yes" in self.sa):
            b=True
        elif(self.current_driver_id==p.PLID):
            b=True
            
        if(b):
            self.print_log('^1HLV:^7 '+reason[p.HLVC]+' '+self.get_driver(p.PLID).get_playername()+' Sp: '+str(float(p.C.Speed)),True)
      
    def obj_contact(self, insim, info):
        InsimClient.obj_contact(self, insim, info)
        b=False
        if("yes" in self.sa):
            b=True
        elif(self.current_driver_id==info.PLID):
            b=True
            
        if(b):
            self.print_log('^2OBH PACKET:^7 CSp='+ str(float(info.SpClose)/10)+' '+self.get_driver(info.PLID).get_playername(),True)
   
        #self.sendMsg('^2OBH PACKET:^7 Closing speed='+ str(info.SpClose/10),'')
    def car_contact (self, insim, info):
        InsimClient.car_contact(self, insim, info)
        
        b=False
        if("yes" in self.sa):
            b=True
        elif(self.current_driver_id==info.A.PLID or self.current_driver_id==info.B.PLID):
            b=True
            
            
        if(b):
             
            self.print_log('^3Car contact:^7 CSp='+ str(float(info.SpClose)/10)+' A= '+self.get_driver(info.A.PLID).get_playername()+' B '+self.get_driver(info.B.PLID).get_playername(),True)

        #self.sendMsg('^3CON PACKET:^7 CSp='+ str(info.SpClose/10),'')