'''
Created on Dec 15, 2010

@author: jason
'''
from pyinsim import IS_NCN, IS_NPL

class Driver:
    '''
    Represents a driver
    '''
    
    def __init__(self,ncon=None):
        self.player_id=0
        self.con_id=0
        self.status=2
        self.lapsdone=0
        self.playername=''
        self.username=''
        self.laptime=[]
        self.splittime={}#dictionary for splits time
        self.current_split=0
        self.bestlap=0
        self.pits=[0,0,0,0,0,0,0,0,0,0,0]
        self.pits_laps=[0,0,0,0,0,0,0,0,0,0,0]
        self.numpits=0
        self.elapsedtime=0
        self.node=-1
        self.position=100
        self.numpitstops=0
        #world coordinates
        self.worldpos=(0,0,0)
        self.worldpos_old=(0,0,0)
        self.car_speed=0.0
        self.car_name=''
        self.tyre_compounds=[]
        self.con_flags=-1
        if(isinstance(ncon, IS_NCN)):
            self.playername=ncon.PName
            self.username=ncon.UName
            self.con_id=ncon.UCID
            self.con_flags=ncon.Flags
        elif(isinstance(ncon, IS_NPL)):
            self.con_id=ncon.UCID
            self.player_id=ncon.PLID
            self.playername=ncon.PName
        
        self.playername=self.playername.decode("latin-1")
        
    def get_playername(self):
        pn=self.playername
        try:
            pn=self.playername.decode("latin-1").encode("utf-8")
            pn=self.playername.encode("utf-8")#TODO this
        except:
            print "ERROR decoding"
        return pn
                            
    def set_laptime(self,laptime, lapsdone, elapsedtime,numpits ):
        #print 'Changing laptime to '+self.playername
        self.laptime.append(laptime)
        self.elapsedtime=elapsedtime # setting elapsed time
        self.lapsdone=lapsdone #setting lapsdone
        self.numpitstops=numpits # setting numpits
        self.current_split=4#TODO what split is this
        #setting best lap
        if(min(self.laptime)==laptime):
            self.bestlap=laptime    
            
    def set_splittime(self,split_id,splittime,elapsedtime,numpistops):
        self.current_split=split_id
        self.numpitstops=numpistops
        #print 'Changing split time to ' +self.playername
        
        #check if lap's splits space exists
        #TODO what if lapsdone is not set?
        if(self.lapsdone+1 in self.splittime):
            self.splittime[self.lapsdone+1][split_id]=splittime
        else:
            self.splittime[self.lapsdone+1]=[0,0,0,0,0]
            self.splittime[self.lapsdone+1][split_id]=splittime
            
        self.elapsedtime=elapsedtime
       
        
    def set_fuel(self,f):
        self.fuel=f;
        #print self.playername+' Fuel: '+str(self.fuel)
            
    def set_node(self,n):
        self.node=n
        #print self.playername + ' Node: '+str(self.node)
    def set_pitstop(self,work):
        self.pits[self.numpitstops-1]=int(work)
        self.pits_laps[self.numpitstops-1]=self.lapsdone+1
    
    def set_pitlap(self,id,value):
        self.pits_laps[id]=value
        
    def set_numpitstops(self,nump):
        #print 'setting numpits to '+str(nump)
        self.numpitstops=nump
             
    def set_position(self,p):
        self.position=p
        
    def set_worldpos(self,p):
        
        if(not self.worldpos_old==(0,0,0)):
            self.worldpos_old=self.worldpos
        else:
            self.worldpos_old=(p[0]/65536.0,p[1]/65536.0,p[2]/65536.0)
            
        self.worldpos=(p[0]/65536.0,p[1]/65536.0,p[2]/65536.0)
        
    def set_speed(self,sp):
        self.car_speed=sp*100/32768.0
    
    def set_playername(self,nm):
        self.playername=nm[:].decode('latin-1')  
    def print_driver(self):
        print( 'Driver '+self.playername+' uname:'+self.username+' plid:'+str(self.player_id)+' ucid:'+str(self.con_id))
        
                             
    def reset(self):
        self.pits=[0,0,0,0,0,0,0,0,0,0,0]
        self.pits_laps=[0,0,0,0,0,0,0,0,0,0,0]
        self.numpitstops=0
        self.current_split=0
        self.node=-1
        self.position=100
        self.player_id=-1
        self.status=2
        self.lapsdone=0
        self.laptime=[]
        #world coordinates
        self.worldpos=(0,0,0)
        self.worldpos_old=(0,0,0)
        self.car_speed=0.0
        #TODO add others members