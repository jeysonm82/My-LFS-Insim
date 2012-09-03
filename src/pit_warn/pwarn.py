'''
Created on Nov 17, 2011

@author: jason_new
'''
from myinsim.insim_client import InsimClient
import pyinsim


class PitInformant(InsimClient):
    
    def __init__(self):
        InsimClient.__init__(self, "PIT Informant")
        self.version="0.1"
        self.flags=pyinsim.ISF_LOCAL
        self.pits={}
        self.lic=self.config.get('pit_warning','licencia')
        self.posx=self.config.getint('pit_warning','posx')
        self.posy=self.config.getint('pit_warning','posy')
        self.pit_gap = self.config.getint('pit_warning','pit_gap')
        self.curlap=0
               
    def pitstop(self,insim, pt):
        InsimClient.pitstop(self, insim, pt)
        self.curlap=pt.LapsDone+1
        work=pt.Work
        plid=pt.PLID
        cl=0
        
        if(not self.drivers[self.driversID[plid]].username.lower()==self.lic.lower()):
            return
        
        #check if valid pitstop
        prev_pit=self.get_last_validpit()
      
        
        if(prev_pit>0 and (self.curlap-prev_pit)>=self.pit_gap):
            #is valid
            cl=1
        elif(prev_pit==0):
            #is valid, no prev pit reg
            cl=1
        else:
            #is not valid
            cl=0
            #register and exit
            self.pits[self.curlap]=cl
            self.draw_pbut()
            return
        
        #check tyres
        
        #if Tyres==4 then driver changed tyres
        if(pt.Tyres[0]==4):
            cl=2
        
        self.pits[self.curlap]=cl
        self.draw_pbut()
        
        
    def lap_time(self,insim,lap):
        InsimClient.lap_time(self, insim, lap)
        plid=lap.PLID
        if(not self.drivers[self.driversID[plid]].username.lower()==self.lic.lower()):
            return
        self.curlap=lap.LapsDone+1
        self.draw_pbut()
    
    def get_last_validpit(self):
        m=0
        for i in self.pits:
            if(i>m and self.pits[i]>0):
                m=i
                
        return m
    
    def reset(self):
        print 'Resetting'
        self.init_tracker()
        self.request_connection_list()
        self.request_player_list()
        self.pits={}
        self.curlap=0
        self.draw_pbut()
            
    def draw_pbut(self):
        tmp=''
        col=['^1','^7','^5']
        #print self.pits
        for i  in sorted(self.pits.iterkeys()):
            tmp+=col[self.pits[i]]+str(i)+' '
        
        cp=chr(139)+chr(155)
        
        prev_pit=self.get_last_validpit()
            
        if(((self.curlap-prev_pit)>=3 or prev_pit==0) and self.curlap>1):
            cp='^2'+cp
        else:
            cp='^1'+cp
            
        tmp=cp+' '+tmp
        print tmp
        self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=198,
                                BStyle= pyinsim.ISB_DARK | pyinsim.ISB_CLICK|1|pyinsim.ISB_LEFT,
                                T=self.posy, L=self.posx, 
                                W=25, H=8,Text='')
        self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=199,
                                BStyle= pyinsim.ISB_DARK | pyinsim.ISB_CLICK|1|pyinsim.ISB_LEFT,
                                T=self.posy, L=self.posx, 
                                W=25, H=8,Text=tmp)
        
    
    def race_start(self,insim,rsp):
        InsimClient.race_start(self, insim, rsp)
        self.reset()
        
