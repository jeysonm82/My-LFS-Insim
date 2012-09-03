'''
Created on Oct 21, 2011

@author: jason_new
'''
from myinsim.insim_client import InsimClient,WorkDaemon
import string 

import pyinsim
from collections import deque
from threading import Thread
import time
import copy
import pickle
import sys
import traceback
import operator

class Crash_List(InsimClient):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        InsimClient.__init__(self, 'CRASH LIST')
        self.version=0.1
        self.curpage=0
        self.track=''
        self.top=40
        self.left=10
        self.crash_msg_queue=deque([]) #crash msgs queue
        self.warn_color='^1'
        self.last_time_crash=0
        self.crash_list=[]
        self.crash_counter={}       
        self.tmp=0
        self.driver_focus=0
        self.flags=pyinsim.ISF_CON|pyinsim.ISF_OBH
        #read csv, previous crashes
        if(self.config.get("crash_list","read_clist")=="yes"):
            print "reading csv"
            self.read_csv()
            print "Read ",len(self.crash_list), " rows "
            #count crashes
            for cr in self.crash_list:
                self.count_crash(cr.car_A)
                self.count_crash(cr.car_B)
            
        
    def begin(self):
        '''
        begin all stuff
        '''
        WorkDaemon(self.c_warn_led,1, False).start();#run everytime
        self.draw_list_button()
      
        
    def add_crash(self,crash):
        #Check if crash doesn't exist in the list
        addit=True
        for i in self.crash_list:
            if(i.signature==crash.signature):
                addit=False
        if(addit):
            print 'Adding crash'
            self.count_crash(crash.car_A)
            self.count_crash(crash.car_B)
            
            self.crash_list.append(crash)
            
            #BUG: the packet.Time is messed up. so we need to make an additional IS_GTH request to get the rigth crash time
            #we append the crash id in ReqI so later we can assign the  time to the right crash
            
            self.insim.send(pyinsim.ISP_TINY,  SubT=pyinsim.TINY_GTH,ReqI=len(self.crash_list))
    
    def count_crash(self,driver_username):
        '''
        Count crashes  for each driver using a dictionary whose keys are driver unames
        '''
        if (driver_username in self.crash_counter):
            self.crash_counter[driver_username]+=1
        else:
            self.crash_counter[driver_username]=1
            
    def small(self,insim, packet):
        #TODO manage SubT to just care about IS_GTH subtype packets 
        InsimClient.small(self, insim, packet)
        id=packet.ReqI
        t=packet.UVal
        print 'adding time to id ', id+1 ,' time ',t 
        self.crash_list[id-1].c_time=t
        #save in file
        #TODO add if
        self.write_csv()
    
    def chat_message(self,insim,mso):
        InsimClient.chat_message(self, insim, mso)
        msg=mso.Msg
        
        print 'message is ' + msg
    
    def pop_crash_queue(self):
        self.crash_msg_queue.pop()
        
    def car_contact (self, insim, info):
        InsimClient.car_contact(self, insim, info)
        print info
        mcar=info.A
        #track='KY1R'
        
        if(info.SpClose>1):
            driv_a=''
            driv_b=''
            try:
                driv_a=self.drivers[self.driversID[info.A.PLID]].playername
                driv_b=self.drivers[self.driversID[info.B.PLID]].playername
            except:
                print 'Cant locate driver name, maybe this key is deleted PLID A:',str(info.A.PLID),' B ',info.B.PLID
                return
            m= 'Contacto ^7A '+ driv_a+ ' y B'+ driv_b
            
            
            print m
            print info.Time
            self.sendMsg(m)
            
            p=[mcar.X/16, mcar.Y/16 ]
            
            #KY1R Nodes
            t_coords=[[-461,181],[-484,295],[-485 , 681],[-104 , 845],[187 , 594],[ 250 , 260],[54 , -81],[-354 , -57]]
            t_names=['T1','T1-T2','T2','T2-T3','T3','T3-T4','T4','T4-T1']
            #KY1 Nodes
            if(self.track=='KY1'):
                t_coords.reverse()
            
            
            tmp=0
            m=9000000
            t_f=0
            for pl in t_coords:
                p1=pl
                if(t_coords.index(pl)==len(t_coords)-1):
                    #last element
                    p2=t_coords[0]
                else:
                    p2=t_coords[t_coords.index(pl)+1]
                d=self.pointline_dist(p1, p2, p)
                print 'Distance To Line ',tmp, ' D: ',d
                if(d<m):
                    m=d
                    t_f=t_names[tmp]
                    
                tmp+=1
            #print 'Precaucion en ',t_f
            #self.sendMsg('^2Precaucion en '+str(t_f))
            if(self.config.get("crash_list","reg_crash")=="yes"):
                self.crash_msg_queue.appendleft(str(t_f))
                self.last_time_crash=time.time()
                self.add_crash(Crash_event(self.get_driver(info.A.PLID).get_playername(), self.get_driver(info.B.PLID).get_playername(),info.A.PLID,info.B.PLID, float(info.SpClose), p[0],p[1], t_f,info.Time))
                
                #schedule the message destroy
                WorkDaemon(self.pop_crash_queue,10,True).start()#destroy it in ten seconds 
        
    def obj_contact(self, insim, info):
        InsimClient.obj_contact(self, insim, info)
        
            
    def pointline_dist(self, p1, p2, p):
        x0=p1[0]
        y0=p1[1]
        x1=p2[0]
        y1=p2[1]
        x=p[0]
        y=p[1]
        vx = x0-x
        vy = y0-y
        ux = x1-x0
        uy = y1-y0
        
        lnt = ux*ux+uy*uy;

        det = (-vx*ux)+(-vy*uy) 
        if(det<0 or det>lnt):
            ux=x1-x;
            uy=y1-y;
            return min(vx*vx+vy*vy, ux*ux+uy*uy)
      

        det = ux*vy-uy*vx
        return (det*det)/lnt
    def get_track_name(self):
        self.insim.send(pyinsim.ISP_TINY,  SubT=pyinsim.TINY_SST)
    
    def race_state(self,insim, rsp):
        InsimClient.race_state(self, insim, rsp)
        self.track=rsp.Track
        
    def hidden_message(self, insim, msg):
        InsimClient.hidden_message(self, insim, msg)
        msg=msg.Msg
        action=msg
        print action
        if(action=='top_crash'):
            self.draw_top_crashers()
            
    def draw_top_crashers(self):
        tmp=0
        at= sorted(self.crash_counter.iteritems(), key=operator.itemgetter(1), reverse=True)
       
        for i in at :
            tmp+=1
            print tmp,'. ' ,i[0] ,',',i[1]
        
    def draw_list_button(self):
        self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=10,
                                BStyle= pyinsim.ISB_DARK | pyinsim.ISB_CLICK|1,
                                T=self.top+23, L=self.left, 
                                W=15, H=15, 
                                Text='^3 LISTA')
       

 
      
        
    def c_warn_led(self):
        if((time.time()- self.last_time_crash)<5.0  and self.last_time_crash>0):
            self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=150,
                                    BStyle= pyinsim.ISB_DARK ,
                                    T=self.top+14, L=self.left, 
                                    W=12, H=7, 
                                    Text=self.warn_color+'NEW CRASH')
            if(self.warn_color=='^1'):
                self.warn_color='^7'
            else:
                self.warn_color='^1'
        else:
            if(not self.warn_color=='^8'):
                self.warn_color='^8'
                self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=150,
                                        BStyle= pyinsim.ISB_DARK ,
                                        T=self.top+14, L=self.left, 
                                        W=12, H=7, 
                                        Text=self.warn_color+'NEW CRASH')
            
    def print_crash_list(self):
        top=20
        left= 50
        
        #Draw close, refresh
        self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=50,
                                        BStyle= pyinsim.ISB_DARK |pyinsim.ISB_CLICK,
                                        T=top-10, L=left-10, 
                                        W=20, H=7, 
                                        Text="^1 X ^7 Total: "+str(len(self.crash_list)))
        
        self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=51,
                                        BStyle= pyinsim.ISB_DARK |pyinsim.ISB_CLICK,
                                        T=top-10, L=left-10+20, 
                                        W=10, H=7, 
                                        Text="^3<<Prev")
        self.insim.send(pyinsim.ISP_BTN,ReqI=255, ClickID=52,
                                        BStyle= pyinsim.ISB_DARK |pyinsim.ISB_CLICK,
                                        T=top-10, L=left-10+20+10, 
                                        W=10, H=7, 
                                        Text="^3Next>>")
        self.tmp=0
        #draw list
        toshow_list=copy.copy(self.crash_list)
        if(len(toshow_list)>self.curpage*25):
            #toshow_list.reverse()
            toshow_list=toshow_list[self.curpage*25:self.curpage*25+25]
            #toshow_list.reverse()
        
            
        for i in toshow_list:
            #Row, ID, car A, car B, t_sector, time
            tm=pyinsim.time(i.c_time*10)
            tm=str(tm[0])+"h"+str(tm[1])+"m"+str(tm[2])+"s"
            
            #msg="^7"+str(self.tmp+1)+'. ^2CarA: '+i.car_A.encode('utf-8')+'     ^2CarB: '+i.car_B.encode('utf-8')+'     ^3 Sector:^7'+i.t_sector+' ^3 Time: ^7'+str(tm)
            msg="^7"+str(self.tmp+1+self.curpage*25)+'. ^2CarA: '+i.car_A+'      ^2CarB: '+i.car_B+'       Sp:'+str(float(i.closing)/10)+'        ^3 Time: ^7'+str(tm)
            
            try:
                self.insim.send(pyinsim.ISP_BTN,ReqI=self.crash_list.index(i)+1, ClickID=70+self.tmp,
                                        BStyle= pyinsim.ISB_DARK|pyinsim.ISB_CLICK |pyinsim.ISB_LEFT,
                                        T=top+7*self.tmp, L=left, 
                                        W=100, H=7, 
                                        Text=msg)
            except:
                print "Error delivering list"
           
            
            
            
            self.tmp+=1
            
    def button_clicked(self,insim,rsp):
        InsimClient.button_clicked(self, insim, rsp)
        #bclicked
        #print 'Button clicked ID: ' +str(rsp.ClickID) + 'flag: '+str(rsp.CFlags)
        c=rsp.ClickID
        if(c==50):
            #close list
            self.hide_list()
        elif(c==51):
            #prev
            self.hide_list()
                
            self.curpage=max(0,self.curpage-1)
            self.print_crash_list()
        elif(c==52):
            #next
            self.hide_list()
                
            self.curpage=min(len(self.crash_list)/25,self.curpage+1)
            self.print_crash_list()
                
        elif(c==10):
            self.print_crash_list()
            
        else:
            self.hide_list()
            #these are "Go to accident buttons"
            id=rsp.ReqI-1
            print 'Go to accident ',id
            self.go_to_crash(self.crash_list[id])
    
    def hide_list(self):
        self.del_button(50)
        self.del_button(51)
        self.del_button(52)
        for i in range(0,self.tmp):
            self.del_button(70+i)
            self.del_button(170+i)
    
    def go_to_crash(self, crash):
        self.sendMsg('^7Ubicando Contacto A:'+crash.car_A+' y B:'+crash.car_B)
        try:
            plid=crash.car_A_PLID # TODO which involved car to choose
            self.driver_focus=plid
            timestamp=max(crash.c_time-500,0)#5 seconds behind crash time
            rip=pyinsim.IS_RIP(CTime=timestamp, ReqI=100, RName="",MPR=1,Paused=1)
            
            #self.insim.send(pyinsim.ISP_RIP, ReqI=100,RName=0, CTime=crash.c_time)
            self.insim.sendp(rip)              
        except:
            print "ERROR going to crash ", sys.exc_info()[0]
            exc_type, exc_value, exc_traceback = sys.exc_info()
            print sys.exc_info()[0]
            traceback.print_tb(exc_traceback, limit=1, file=sys.stdout)
            traceback.print_exception(exc_type, exc_value, exc_traceback,
                              limit=5, file=sys.stdout)
            print crash
    
    def rip(self, insim, packet):
        InsimClient.rip(self, insim, packet)
        #When we get this it means that we got to our desired crash time
        #So the next thing is to locate the camera on the correct car, that is, driver_focus
        cam=pyinsim.IS_SCC(ReqI=40, ViewPLID=self.driver_focus)
        self.insim.sendp(cam)
    
    def write_csv(self):
        
        print "writing csv"
        f=open("crash_events.pl",'wb')
        pickle.dump(self.crash_list,f)
        f.close()   
    def read_csv(self):
        f=open("crash_events.pl",'rb')
        self.crash_list=pickle.load(f)
        f.close()   
class Crash_event():
    def __init__(self,car_A,car_B, car_A_PLID, car_B_PLID,closing,x,y,t_sector,c_time):
        self.car_A=car_A
        self.car_B=car_B
        self.closing=closing
        self.x=x
        self.y=y
        self.t_sector=t_sector
        self.c_time=c_time
        self.ci_time=c_time
        self.car_A_PLID=car_A_PLID
        self.car_B_PLID=car_B_PLID
        self.signature=str(car_A)+str(car_B)+str(x)+str(y)+str(c_time)
