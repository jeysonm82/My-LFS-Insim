'''
Created on Nov 28, 2011

@author: jason_new
'''
from myinsim.insim_client import InsimClient,WorkDaemon
import pyinsim
import random
import sys
import time
class Custom_Launcher(InsimClient):
    INIT_STATE=0
    CANCELLED_STATE=70
    
    def __init__(self):
        InsimClient.__init__(self, 'CUSTOM LAUNCHER')
        self.version="0.4.1"
        self.print_log("----"+self.tag+" v."+str(self.version) + " started."+"----")
        self.flags=pyinsim.ISF_MCI
        self.num_lights=self.config.getint("custom_launcher", "num_lights")
        self.state=self.num_lights+2
        self.pen_given=[]
        self.tmp=0
        self.interval=self.config.getint("connection", "interval")
        self.sem_styles=[(chr(149),chr(149)),(chr(166)*2,chr(166)*2),('*','*'),("["+chr(149)+"]","["+chr(149)+"]"),(chr(186)*2+' ',chr(186)*2+' '),('#','#')]
        self.bstyle=[0,pyinsim.ISB_LIGHT, pyinsim.ISB_DARK]
        self.launch_tstamp=0
        self.launch_stime=0#launch server time
        self.abort_counter=0
    def semaphore(self):
        color=''
        msg=''
        if (self.state==Custom_Launcher.CANCELLED_STATE):
            return
        print 'state '+str(self.state)
        for i in range(0,self.num_lights):
            if(i<self.state):
                l_style=self.sem_styles[self.config.getint('custom_launcher','l_style')-1][1]
                color='^'+self.config.get('custom_launcher','on_color')
            else:
                l_style=self.sem_styles[self.config.getint('custom_launcher','l_style')-1][0]
                color='^'+self.config.get('custom_launcher','off_color')
            if(self.state==(self.num_lights+1)):
                l_style=self.sem_styles[self.config.getint('custom_launcher','l_style')-1][1]
                #num_lights +1 in this state the lights, being on,  change it color and the race start indmediatly 
                color='^'+self.config.get('custom_launcher','start_color')
            #msg+=color+chr(149)+' '
            msg+=color+l_style+' '
        msg=msg[:-1]
        self.insim.send(pyinsim.ISP_BTN,ReqI=1, ClickID=100,UCID=255,
                                BStyle= self.bstyle[self.config.getint('custom_launcher','bstyle')] ,
                                T=self.config.getint('custom_launcher','posy'), L=self.config.getint('custom_launcher','posx'), 
                                W=self.config.getint('custom_launcher','width'), H=self.config.getint('custom_launcher','height'), 
                                Text=msg)#Button
        self.state+=1
        if(self.state==1):
            #All lights are off. First wait
            self.print_log("Indicator deployed. All lights off.")
            t=self.gettime('wait_time')
            WorkDaemon(self.semaphore, random.uniform(t[0],t[1]), True).start()
            
        elif(self.state<(self.num_lights+1)):
            #lights are being turned on
            self.print_log("Light "+str(self.state-1)+" turned on.")
            t=self.gettime('light_time')
            WorkDaemon(self.semaphore, random.uniform(t[0],t[1]), True).start()
       
        elif(self.state==(self.num_lights+1)):
            #all lights on. This is the last wait
            self.print_log("Light "+str(self.state-1)+" turned on. All lights on. Final delay started.") 
            t=self.gettime('start_time')
            WorkDaemon(self.semaphore, random.uniform(t[0],t[1]), True).start()
       
        elif(self.state==(self.num_lights+2)):
            #Already green flag, set new thread to delete the flag later
            print 'CAN START'
            t=time.time()
            est=pyinsim.time(int(self.launch_stime+round(t-self.launch_tstamp,4)*1000))
            est=str(est[0])+'h'+str(est[1]) +'m'+str(est[2])+'.'+str(est[3])+'s'       
            m=self.config.get('custom_launcher','start_msg')
            
            if(not m==''):
                self.sendMsg(m, ap='')
                     
            self.print_log("RACE STARTED."+' (EST: '+est+')')
            t=self.gettime('show_time')
            WorkDaemon(self.clear_semaphore, t[0], True).start()
            
    def clear_semaphore(self):
        self.print_log("Indicator cleared.")
        if (self.state==Custom_Launcher.CANCELLED_STATE):
            return
        self.del_button(100)
        
    def launch_semaphore(self):
        print 'Launching race'
        self.print_log("Starting Launch sequence")
        self.num_lights=self.config.getint("custom_launcher", "num_lights")
        print "number of lights: ",self.num_lights
        self.state=Custom_Launcher.INIT_STATE #first state
        self.pen_given=[]
        self.launch_tstamp=time.time()
        #request server time
        self.request_server_time()
        self.abort_counter=0
        self.semaphore()
    
    def request_server_time(self):
        self.insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_GTH)
        
    def recv_MCI(self,insim, rsp):
        InsimClient.recv_MCI(self, insim, rsp)
        #print "Receiving MCI ",round(time.time()-self.tmp,4)*1000
        self.tmp=time.time()
        pen=self.config.get('custom_launcher','penalty')
        c_on_j=self.config.get('custom_launcher','cancel_on_jumpstart')
        
        if (self.state>=(self.num_lights+2)):
            return #green flag already
        abort_start=False
        try:
            t=time.time()
            #Check all drivers, 0.26 is 1 km/h aprox.
            for i in self.drivers:
                if( self.drivers[i].car_speed>=0.26):
                    if( self.drivers[i].username not in self.pen_given):
                        
                        self.pen_given.append(self.drivers[i].username)
                        #send penalty
                        if((not pen=='none') or c_on_j=='no'):
                            if((not pen=='none')):
                                self.print_log("Penalizing driver "+self.drivers[i].playername+ " for jumpstart.")
                                self.sendMsg(self.drivers[i].username, '/'+pen+' ')
                        
                        #calculate EST
                    
                        est=pyinsim.time(int(self.launch_stime+round(t-self.launch_tstamp,4)*1000))
                   
                        est=str(est[0])+'h'+str(est[1]) +'m'+str(est[2])+'.'+str(est[3])+'s'       
                        self.print_log('Jumpstart of '+self.drivers[i].playername+' License: '+self.drivers[i].username.decode('latin-1') + ' Car speed:'+str(round(self.drivers[i].car_speed/0.26,3))+' (EST: '+est+')')        
                        self.sendMsg('^7'+self.config.get('custom_launcher','msg1')+' '+self.drivers[i].playername)
                       
                        if(c_on_j=='yes' and self.state<Custom_Launcher.CANCELLED_STATE):
                            abort_start=True
                    
                    #print 'Jump of '+self.drivers[i].playername
                    #print 'Speed ',self.drivers[i].car_speed
                    #print '---'
            if(abort_start):
                self.cancel_start()
        except:
            print '[ERROR]: Error dealing with MCI packets.'
            print "Unexpected error:", sys.exc_info()[0]
    
    def cancel_start(self):
        if(self.abort_counter>0):
            return
        
        self.abort_counter=1
        WorkDaemon(self.cancel_start_t, interval=0.35, run_once=True).start()
    def cancel_start_t(self):
        self.state=Custom_Launcher.CANCELLED_STATE

        msg=(('^3'+self.sem_styles[self.config.getint('custom_launcher','l_style')-1][1]+' ')*self.num_lights)[:-1]
        #msg='^3'+chr(149)+' ''^3'+chr(149)+' ''^3'+chr(149)+' ''^3'+chr(149)
        self.insim.send(pyinsim.ISP_BTN,ReqI=1, ClickID=100,UCID=255,
                                BStyle= self.bstyle[self.config.getint('custom_launcher','bstyle')] ,
                                T=self.config.getint('custom_launcher','posy'), L=self.config.getint('custom_launcher','posx'), 
                                W=self.config.getint('custom_launcher','width'), H=self.config.getint('custom_launcher','height'), 
                                Text=msg)#Button
        self.sendMsg(self.config.get('custom_launcher','cancel_msg'),'')
        self.print_log("START CANCELLED.")

    def gettime(self, tag):
        t=self.config.get('custom_launcher',tag).split(',')
        if(len(t)==1):
            t+=t
            
        for i in range(0,len(t)):
            t[i]=float(t[i])
        return t
    
    def recv_tiny(self,insim, p):
        InsimClient.recv_tiny(self, insim, p)
        if(p.SubT==4):
            print 'pong ',round(time.time()-self.tmp,4)*1000,'ms'
    
    def others(self,insim, packet):
        t=time.time()
        print "GTH (Server time) ",packet.UVal*10, pyinsim.time(packet.UVal*10)
        cor=round(t-self.launch_tstamp,4)
        print " Sync by ",  cor*1000, 'ms'
        stime= packet.UVal*10
        if(stime==0):
            self.launch_stime=0
            return
        stime-=cor*1000
        stime=int(stime)
        print "GTH (Final) ",stime,' ',pyinsim.time(stime)
        self.launch_stime=stime
             
    def hidden_message(self, insim, msg):
        InsimClient.hidden_message(self, insim, msg)
        m=msg.Msg
      
        
        if(m=='launch'):
            if(self.state==Custom_Launcher.INIT_STATE or self.state>=(self.num_lights+2)):
                self.launch_semaphore()
        elif(m=='cancel'):
            if(self.state>Custom_Launcher.INIT_STATE and self.state<=Custom_Launcher.CANCELLED_STATE):
                self.cancel_start()
        elif(m=='clear'):
            self.del_button(100)#TODO fix flag issue
            self.state=(self.num_lights+2)
        elif (m=='ping'):
            self.tmp=time.time()
            self.insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_PING)
        elif(m=='gth'):
            self.insim.send(pyinsim.ISP_TINY, ReqI=255, SubT=pyinsim.TINY_GTH)

            