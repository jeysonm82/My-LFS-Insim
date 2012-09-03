'''
Created on Dec 14, 2010
Insim Client. Core of the system. Your class must inherit from this one
@author: jason
'''
import pyinsim
from threading import Thread
import math
import base64
import os
from driver import Driver
import ConfigParser
import string
from time import localtime, strftime
import time

class InsimClient:
    '''
    InsimCLient. This is the Core class that is on top of pynsim. Also, it implements a tracker that maintains a list of driver objects (see driver.py) where each one represents a driver on track.  Inherit this class to create your insim
    '''
    def __init__(self,tag=''):
        #TODO configurations
        self.tag=tag
        print 'INSIM:  '+tag
        self.interval=300#MCI interval
        self.start_time=time.time()
        self.a=[]#TODO what is this?
        self.current_driver_fuel=0.0
        self.tag=tag
        self.current_driver_id=0
        self.race_type=0
        self.race_laps=0
        self.connected=False
        self.traker_enabled=False
        self.outg_enabled=False
        self.outs_enabled=False
        
        #read configuration file
        self.config = ConfigParser.ConfigParser()
        self.config.read('./config.cfg')
        self.flags=''#connection flags
        self.ip=self.config.get('connection','ip')
        self.port=self.config.getint('connection','port')
        self.passw=self.config.get('connection','pass')
        self.insim=''
        self.version=''
        self.admins={}
 
    def init_tracker(self):
        '''
        Initializes the tracker (dictionary that contains drivers data). The list is always synchronized
        '''
        print('INIT TRACKER')
        self.traker_enabled=True
        self.drivers={}#dictionary for driver id PLID
        self.driversID={}#dictionary for connection, PLID
        self.pos_drivers=[0]*47#to store drivers id sorted by position
    def init_outgauge(self,port=30000,interval=100):
        print "INIT OUTGAUGE"
        self.outgauge_port=port
        self.outgauge_interval=interval
        self.outg_enabled=True
        
    def init_outsim(self,port=30001,interval=100):
        print "INIT OUTSIM"
        self.outsim_port=port
        self.outsim_interval=interval
        self.outs_enabled=True
        
    def connect(self,f=''):
        '''
        Connect to server using self.flags (or default)
        '''
        #TODO configurations
        
        if(self.flags==''):
            self.flags= pyinsim.ISF_CON|pyinsim.ISF_MCI #contact
        print 'Connecting to '+str(self.ip), "flags ",self.flags
        self.insim = pyinsim.insim(self.ip, self.port, Admin=self.passw,Flags=self.flags,Interval=self.interval)
        
        #TODO flag to enable, disable outgauge
        if(self.outg_enabled):
            print "Initializing outgauge port: ",self.outgauge_port, " int: ",self.outgauge_interval
            self.outgauge = pyinsim.outgauge('127.0.0.1', self.outgauge_port, self.outgauge_packet, self.outgauge_interval)
        
        if(self.outs_enabled):
            print "Initializing Outsim port: ",self.outsim_port, " int: ",self.outsim_interval
            self.outsim= pyinsim.outsim('127.0.0.1', self.outsim_port, self.outsim_packet, self.outsim_interval)
        
        self.__bindEvents()
        #self.run()
        
        #we need to request connections and players 
        self.request_connection_list()
        self.request_player_list()
        self.sendMsg(self.tag +' V.'+ str(self.version)+ " started.")
   
         
    def outgauge_packet(self,outgauge, packet):
        #TODO check if fuel packet is from local driver
        self.current_driver_fuel=packet.Fuel
        
        
        #self.drivers[self.driversID[self.current_driver_id]].set_fuel(packet.Fuel)
         
    def outsim_packet(self,outsim, packet):
        pass
        
    def run(self,b):
        pyinsim.run(b)    
        
    def race_start(self,insim,rsp):
        '''
        ISP_RST
        '''
        #TODO, RESET?
        print('Race starting')
        
        self.drivers={}#dictionary for driver id PLID
        self.driversID={}#dictionary for connection, PLID
        self.pos_drivers=range(1,47)#to store drivers id sorted by position
        
        for i in range(0,46):
            self.pos_drivers[i]=0 #TODO ugly code
   
        self.request_connection_list()
        self.request_player_list()
        
    def print_all_drivers(self):
        '''
        print drivers
        '''
        print 'printing all drivers'
                
        for drv in self.drivers:
            #drv.print_driver()
            self.drivers[drv].print_driver()
        
                
    def __bindEvents(self):
        '''
        Binds events
        '''
        self.insim.bind(pyinsim.ISP_MSO,self.chat_message)
        self.insim.bind(pyinsim.EVT_INIT, self.init)
        self.insim.bind(pyinsim.EVT_CLOSE, self.closed)
        self.insim.bind(pyinsim.EVT_ERROR, self.error)
        self.insim.bind(pyinsim.ISP_SPX,self.split_time)
        self.insim.bind(pyinsim.ISP_LAP,self.lap_time)
        self.insim.bind(pyinsim.ISP_NCN, self.new_connection)
        self.insim.bind(pyinsim.ISP_CNL, self.connection_left)
        self.insim.bind(pyinsim.ISP_NPL, self.new_player)
        self.insim.bind(pyinsim.ISP_STA, self.race_state)
        self.insim.bind(pyinsim.ISP_PLL, self.player_left)
        self.insim.bind(pyinsim.ISP_PLP,self.player_pitted)
        self.insim.bind(pyinsim.ISP_PIT,self.pitstop)
        self.insim.bind(pyinsim.ISP_PSF,self.pitfinished)
        self.insim.bind(pyinsim.ISP_MCI,self.recv_MCI)
        self.insim.bind(pyinsim.ISP_RST,self.race_start)
        self.insim.bind(pyinsim.ISP_BTC, self.button_clicked)
        self.insim.bind(pyinsim.ISP_BTT, self.button_typed)
        self.insim.bind(pyinsim.ISP_TOC,self.take_over)
        self.insim.bind(pyinsim.ISP_FIN,self.race_finished)
        self.insim.bind(pyinsim.ISP_III,self.hidden_message)
        self.insim.bind(pyinsim.ISP_CON,self.car_contact)
        self.insim.bind(pyinsim.ISP_FLG,self.flag_caused)
        self.insim.bind(pyinsim.ISP_OBH, self.obj_contact)
        self.insim.bind(pyinsim.ISP_SMALL, self.small)
        self.insim.bind(pyinsim.ISP_RIP,self.rip)
        self.insim.bind(pyinsim.ISP_CPR, self.player_rename)
        self.insim.bind(pyinsim.ISP_HLV, self.hlv)
        self.insim.bind(pyinsim.ISP_TINY, self.recv_tiny)
    
    def recv_tiny(self,insim, p):
        pass
    
    def hlv(self,insim, p):
        '''
        ISP_HLV
        '''
        #print p
        pass

    def player_rename(self, insim , info):
        '''
        ISP_CPR
        '''
        if(self.traker_enabled==False):
            return
        try:
            self.drivers[info.UCID].set_playername(self.PName)
            print 'Player UCID ', info.UCID, ' renamed to ',self.drivers[info.UCID].playername
        except:
            print 'Error renaming UCID ', info.UCID

    def rip(self, insim, packet):
        '''
        ISP_RIP
        '''
        print 'Time is ',packet.TTime, ' Req ',packet.ReqI, ' Error ',packet.Error,' name ',packet.RName
    
    def small(self,insim, packet):
        '''
        ISP_SMALL
        '''
        print 'Other packet received ',packet, ' value ',packet.UVal
        

    
    def obj_contact(self, insim, info):
        '''
        ISP_OBH
        '''
        pass
    
        
    def flag_caused (self, insim, flag):
        '''
        ISP_FLG
        '''
        #print 'Flag ',flag.Flag,' Driver ',self.drivers[self.driversID[flag.PLID]].playername, ' Behind ', flag.CarBehind
        pass
    
    def car_contact (self, insim, info):
        '''
        ISP_CON
        '''
        pass
        
    def hidden_message(self, insim, msg):
        '''
        ISP_III
        Hidden message received
        '''
        if(msg.Msg=='version' or msg.Msg=='ver'):
            print 'requesting version'
            self.insim.send(pyinsim.ISP_MTC, UCID=msg.UCID, Msg="^3"+self.tag + ' ^7version: '+str(self.version))
            self.insim.send(pyinsim.ISP_MSL, Msg="^3"+self.tag + ' ^7version: '+str(self.version))
        elif(msg.Msg=="terminar" or msg.Msg=='exit'):#TODO exit + program tag
            self.exit_app()
        elif(msg.Msg=="ping"):
            print 'ping pong'
            self.insim.send(pyinsim.ISP_MTC, UCID=msg.UCID, Msg="^3"+self.tag + ' ^7pong:'+str(time.time()))
            self.insim.send(pyinsim.ISP_MSL, Msg="^3"+self.tag + ' ^7pong: '+str(time.time()))
        elif(msg.Msg=='reload_config'):
            print 'reloading configuration.'
            self.config = ConfigParser.ConfigParser()
            self.config.read('./config.cfg')
            
    def exit_app(self):
        pyinsim.closeall()
        exit()
                
    def race_finished(self,insim, rsp):
        '''
        ISP_FIN
        '''
        pass
        
    def take_over(self,insim,rsp):
        '''
        ISP_TOC
        '''
        print "Take over"
        self.driversID[rsp.PLID]=rsp.NewUCID
        if(self.drivers[rsp.NewUCID] is  None):
                self.drivers[rsp.NewUCID]=Driver()
                
        
        self.drivers[rsp.NewUCID].player_id=rsp.PLID
        self.drivers[rsp.NewUCID].estado=2

    def del_button(self,id,ucid=255):
        '''
        Deletes id button to player ucid
        '''
        #print 'Deleting button ID: ',id
        self.insim.send(pyinsim.ISP_BFN,ClickID=id,SubT=0, UCID=ucid)
    
    def button_typed(self,insim,rsp):
        '''
        ISP_BTT
        '''
        #whe user types in buttons (TypeIn set)
        #print 'Type: '+rsp.Text+' CID'+str(rsp.ClickID)
        a=1
        
            
    def recv_MCI(self,insim, rsp):
        '''
        Receives MCI packets
        '''
        if(self.traker_enabled==False):
            return
    
        #receive MCI
        m=0
        mid=0     
        for car in rsp.Info:
            #stry='Speed: '+str(car.Speed)+' PLID: '+str(car.PLID)+' Position:'+str(car.Position)+' Node:'+str(car.Node)
            #print stry
            if(car.PLID in self.driversID and car.PLID>0):
               
                if(self.drivers[self.driversID[car.PLID]] is not None):
                    self.drivers[self.driversID[car.PLID]].set_node(car.Node)
                    self.drivers[self.driversID[car.PLID]].set_position(car.Position)
                    self.pos_drivers[car.Position]=self.driversID[car.PLID]
                    #self.drivers[self.driversID[car.PLID]].set_worldpos((car.X,car.Y,car.Z)) #TODO this
                    self.drivers[self.driversID[car.PLID]].set_speed(car.Speed)
                    #print "PLID, ",car.PLID
                    #print (car.X,car.Y,car.Z)
         

        #self.print_all_drivers()
       
    def race_state(self,insim, rsp):
        '''
        ISP_STA
        '''
        print ("Race state changed")
        self.race_type=rsp.RaceInProg
        self.race_laps=rsp.RaceLaps
        self.current_driver_id=rsp.ViewPLID
            
            
    def chat_message(self,insim,mso):
        '''
        Receives ISP_MSO
        chats and /msg, and every other visible message 
        '''
        
        print(mso.Msg)
        #BUG take over rename. (workaround)
        if(string.count(mso.Msg,'took over from')>0):
            #print 'A took over ocurred, requesting connections'
            self.request_connection_list()
                    
            
        
    def init(self,insim):
        '''
        Receives EVT_INIT
        '''
        print('Connected')
        self.connected=True
                
    def closed(self,insim):
        '''
        Receives EVT_CLOSED
        '''         
        print('Closed')
        
    def error(self,insim):
        print('Error')
    
    def split_time(self,insim,split):
        '''
        Receives ISP_SPX
        '''
        #print('Split time: ' + str(split.STime) + ' PLID: ' + str(split.PLID)+ 'ETIME: '+str(split.ETime))
        if(self.traker_enabled==False):
            return
        try:
            self.drivers[self.driversID[split.PLID]].set_splittime(split.Split, split.STime,split.ETime,split.NumStops)
        except:
            print 'recvSplittime, Key_error, driver PLID',split.PLID,' doesnt exist, please check'            

        
        
    def lap_time(self,insim,lap):
        '''
        Receives ISP_LAP
        '''
        
        #print ('Lap Time '+ str(lap.LTime)+' PLID: ' + str(lap.PLID))
        
      
        if(self.traker_enabled==False):
            return
        try:
            self.drivers[self.driversID[lap.PLID]].set_laptime(lap.LTime,lap.LapsDone,lap.ETime,lap.NumStops)
        except:
            print 'recvLaptime, Key_error, driver PLID',lap.PLID,' non existent, plese check'            

        
    def pitstop(self,insim, pt):
        '''
        ISP_PIT
        '''
        
        #pt=pyinsim.IS_PIT()
        if(self.traker_enabled==False):
            return
        
        #print 'Work: '+str(pt.Work)
        #print 'pstop '+str(pt.NumStops)
        #print self.dec2listbin(int(pt.Work))
        try:
            self.drivers[self.driversID[pt.PLID]].set_numpitstops(pt.NumStops)
            self.drivers[self.driversID[pt.PLID]].set_pitstop(pt.Work)
        except:
            print 'Key_error, driver PLID',pt.PLID,' non existent, plese check'            

            
      
   
    def pitfinished(self,insim,pf):
        '''
        ISP_PSF
        '''
        #pf=pyinsim.IS_PSF()
        
        #print 'Fin pit:  '+ str(pf.STime)
        #print 'Spare:  '+ str(pf.Spare)
        pass
    
    
    def dec2listbin(self,n):
        '''convert denary integer n to binary string bStr'''
        bStr = ''
        if n < 0:  raise ValueError, "must be a positive integer"
        if n == 0:
            return list(str(0))
        while n > 0:
            bStr = str(n % 2) + bStr
            n = n >> 1
        return list(str(bStr))
        
        
                    
    def sendChat(self,msg):
        self.insim.send(pyinsim.ISP_MST,Msg=msg)
        
    def sendMsg(self,msg, ap='/msg ', ucid=255):
        '''
        ISP_MST
        Sends msg 
        '''
        #print msg
        msg=msg.encode('latin-1')
        if(ucid==255):
            self.insim.send(pyinsim.ISP_MST,Msg=ap+msg)
        else:
            self.insim.send(pyinsim.ISP_MTC,Msg=msg,UCID=ucid, Sound=pyinsim.SND_MESSAGE)
    def send_RCM(self,msg):
        '''
        RCM
        '''
        self.insim.send(pyinsim.ISP_MST,Msg='/rcc_all '+msg)    
        self.insim.send(pyinsim.ISP_MST,Msg='/rcm '+msg)
        self.insim.send(pyinsim.ISP_MST,Msg='/rcm_all '+msg)
        
    def send_button(self,id=1,top=20,left=20,width=20, height=10,msg='test',ucid=255,bs=pyinsim.ISB_CLICK | pyinsim.ISB_DARK,typein=0):
        '''
        Sends button
        use pyinsim.ISB in bs to set style
        '''
        self.insim.send(pyinsim.ISP_BTN, 
           ReqI=255, 
           ClickID=id,
           UCID=ucid, 
           BStyle=bs,
           T=top, 
           L=left, 
           W=width, 
           H=height,
           TypeIn=typein, 
           Text=msg)
                 
    def new_connection(self,insim, ncn):
        '''
        Receives ISP_NCN
        Adds a new connection to the connections dict.
        '''
        
        #connections[ncn.UCID] = ncn
        print 'New connection: %s' % ncn.UName
        
        if(self.traker_enabled==False):
            return
        
        if(ncn.UCID>=0):
            if(ncn.UCID not in self.drivers):
                print 'Adding new driver UCID: ' +str(ncn.UCID)
                self.drivers[ncn.UCID]=Driver(ncn)
            else:
                #refreshing driver
                print 'refreshing driver UCID: ' +str(ncn.UCID)
                self.drivers[ncn.UCID].set_playername(ncn.PName)
                
        if(ncn.Admin==1):
            print "Adding Admin"
            self.admins[ncn.UName]=ncn.UCID
    def connection_left(self,insim, cnl):
        '''
        ISP_CNL
        '''
        
        if(self.traker_enabled==False):
            return
        
        # Get connection from connections dict.
        # Delete the connection from the dict.
        #del connections[cnl.UCID]
        if(cnl.UCID>0):
            print 'Connection left: %s' % cnl.UCID
            if (cnl.UCID in self.drivers):
                del self.drivers[cnl.UCID]
        
    
    def new_player(self,insim, npl):
        '''
        ISP_NPL
        Add the new player to the players dict.
        '''
        #players[npl.PLID] = npl
        try:
            print 'New player: %s' % pyinsim.stripcols(npl.PName)
            
            if(self.traker_enabled==False):
                return
            
            if(npl.UCID==0):
                print('Warning Tracker doesnt work well in offline mode. Do not use AIs in offline mode')
                #self.tracker=False
                #self.exit_app()
            
            print 'Driver name '+ npl.PName + " UCID: "+str(npl.UCID)+ " PLID: "+str(npl.PLID) 
            if(self.drivers[npl.UCID] is  None):
                
                self.drivers[npl.UCID]=Driver(npl)
                
            self.driversID[npl.PLID]=npl.UCID
            
            self.drivers[npl.UCID].player_id=npl.PLID
            self.drivers[npl.UCID].status=2
            self.drivers[npl.UCID].car_name=npl.CName
            self.drivers[npl.UCID].tyre_compounds=npl.Tyres
            self.drivers[npl.UCID].set_playername(npl.PName) 
            #self.print_all_drivers()
        except:
            print "Key error"
           
    def player_pitted(self,insim,ppit):
        '''
        ISP_PLP
        '''
        print 'Player pitted: %s' % (ppit.PLID)
        
        if(self.traker_enabled==False):
            return
        try:
            self.drivers[self.driversID[ppit.PLID]].lapsdone=0
            self.drivers[self.driversID[ppit.PLID]].status=1
            self.drivers[self.driversID[ppit.PLID]].position=100
        except:
            print 'Key_error, driver PLID',ppit.PLID,' non existent, please check'            
                
    def player_left(self,insim, pll):
        '''
        ISP_PLL
        '''
        # Get player from the players dict.
        # Delete him from the dict.
        #del players[pll.PLID]
        print 'Player left: %s' % (pll.PLID)
        
        if(self.traker_enabled==False):
            return
        try:
            self.drivers[self.driversID[pll.PLID]].reset()
            self.drivers[self.driversID[pll.PLID]].position=100
            del self.driversID[pll.PLID]
        except:
            print 'Key_error, driver PLID',pll.PLID,' non existent, please check'            
     
    def request_connection_list(self):
        self.insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_NCN)
        
    def request_player_list(self):
        self.insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_NPL)
    
    def button_clicked(self,insim,rsp):
        '''
        ISP_BTC
        '''
        #bclicked
        print 'Button clicked ID: ' +str(rsp.ClickID) + 'flag: '+str(rsp.CFlags)
    
    def get_driver(self,plid):
        '''
        Get driver by PLID 
        '''
        try:
            return self.drivers[self.driversID[plid]]
        except:
            print "Error. Driver PLID:",plid, " doesn't exist"
            return None
    
    def get_driver_by_uname(self,uname):
        '''
        Get driver by username
        '''
        for i in self.drivers:
            if(self.drivers[i].username==uname):
                return self.drivers[i]
        
        print "Error Driver UNAME: ", uname, "doesn't exist."
        return None
    
    def print_log(self,msg,send_msg=False,cur_driver=0):
        '''
        Log message. send_msg flag to send the msg with /msg as well.  
        '''
        if(cur_driver>0 and self.current_driver_id!=cur_driver):
            return
        a=open('./log_'+str(self.tag)+'.txt','a')
        #msg=str(msg )
        if(send_msg):
            self.sendMsg(msg,'')
            #self.sendMsg(" (ET: "+str(round(time.time()-self.start_time,4)), '/msg')
            #print(str(msg),'')
            #print(" (ET: "+str(round(time.time()-self.start_time,4)), '/msg')
        try:
            s2w=(strftime("%Y-%m-%d %H:%M:%S", localtime())+': '+msg+" (ET: "+str(round(time.time()-self.start_time,4))+")"+str('\r\n'))
            s2w=s2w.encode('utf-8', 'replace')
            a.write(s2w)
        except:
            print "Error adding line to LOG."
            print "This line: ",s2w
        a.close()
    
class WorkDaemon(Thread):
    '''
    A daemon thread
    '''
    def __init__(self,work_method, interval,run_once=False,params=None,run_first_time=True):
        '''
        @param work_method: the referenced method/function.
        @param interval: interval in seconds
        @run_once: True if the process is ment to run only once  
        '''
        Thread.__init__(self)
        self.work_method=work_method
        self.daemon=True
        self.interval=interval
        self.paused=False
        self.run_once=run_once
        self.once_counter=0
        self.params=params
        self.idt=base64.urlsafe_b64encode(os.urandom(4))
        #print 'Thread created Run once ', self.run_once
        self.stopped=False
        self.run_first_time=run_first_time
    
    def run(self):
        
        while(True):
            if(self.stopped):
                return
            if(not self.paused):
                if(self.once_counter==0 and self.run_first_time==False):
                    self.once_counter+=1        
                    time.sleep(self.interval)
                    continue
                
                if(not self.run_once):
                    #print 'Excuting ',self.idt
                    if(self.params==None):
                        self.work_method()
                    else:
                        self.work_method(self.params)
                        
                elif(self.once_counter==1):
                    #print 'Executing once ',self.idt
                    if(self.params==None):
                        self.work_method()
                    else:
                        self.work_method(self.params)
                    return #execute just 1 one time after first interval comes up  
            #print('Incrementing once counter')    
            self.once_counter+=1        
            time.sleep(self.interval)
    def pause(self):
        self.paused=True
        
    def unpause(self):
        self.paused=False
        
    def stop(self):
        self.stopped=True
                        
   
