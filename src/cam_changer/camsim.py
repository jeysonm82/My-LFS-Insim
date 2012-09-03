'''
Created on Feb 14, 2012

@author: jason_new
'''
from myinsim.insim_client import InsimClient,WorkDaemon
import pyinsim
import random
import time
import shutil
import os
class Cam_Sim(InsimClient):
    
    def __init__(self):
        InsimClient.__init__(self, "Cam_Changer")
        self.version=0.2
        self.cur_carcam=0
        #self.cams=[pyinsim.VIEW_CAM,pyinsim.VIEW_HELI,pyinsim.VIEW_DRIVER,pyinsim.VIEW_CUSTOM]
        self.cams=[str(x) for x in self.config.get("cam_changer","cams").split(",")]
        self.flags=pyinsim.ISF_LOCAL|pyinsim.ISF_MCI #TODO we need MCI for position. FIX
        self.ccam_t=None
        self.ccar_t=None
        self.msg="^7THis is example test."
        self.c_count=1
    
    def draw_big_button(self):
        m=""
        ic=self.config.get("cam_changer","im")
        p=[int(x) for x in self.config.get("cam_changer","props_tb").split(",")]
        cpt=self.config.getint("cam_changer","cpt")
        
        for i in range(self.c_count,min(self.c_count+cpt,32+1)):
            if(self.pos_drivers[i]>0):
                m+="^6"+str(i)+". "+self.drivers[self.pos_drivers[i]].playername.encode("latin-1")+" "
       
        if(m==""):
            self.c_count=1
            self.send_button(147, p[1],p[0], p[2], p[3],msg=ic,bs=pyinsim.ISB_DARK)
            return
        if(self.c_count==31):
            m+=" "*4+ic    
        self.send_button(147, p[1],p[0], p[2], p[3],msg=m,bs=pyinsim.ISB_LEFT|pyinsim.ISB_DARK)
        
        self.c_count+=cpt
        self.c_count=min(self.c_count,32)
        if(self.c_count==32):
            self.c_count=1
            
    def change_carcam(self):
        scam=self.cams[self.cur_carcam]
        print "Changing car camera. ",scam

        if(self.iscustom(scam)):
            #custom cam
            self.set_custom_cam(scam)
            self.sendMsg("/view custom", '')
        
            self.sendMsg("/view reload", "")#again, not sure
            
        else:
            #normal cam, set
            self.sendMsg("/view "+scam, '')
        
        if(not self.config.get("cam_changer","random")=="yes"):
            if(self.cur_carcam<len(self.cams)-1):
                self.cur_carcam+=1
            else:
                self.cur_carcam=0
        else:
            #random
            self.cur_carcam=random.randint(0, len(self.cams)-1)
    
    def iscustom(self,cam):
        if(cam=="cam" or cam=="fol" or cam=="heli" or cam=="driver"):
            return False
        return True
    
    def set_custom_cam(self,scam):
        #replace files
        orig="./cams/"+scam+"/"
        dr=os.listdir(orig)
        dst=self.config.get("cam_changer","lfs_path")
        print "Setting up Custom cam."
        
        try:
            for i in dr:
                shutil.copy("./cams/"+scam+"/"+i, dst+"data/views/"+i)
            self.sendMsg("/view reload", "")
            
        except:
            print "Error copying custom camera files" 
         
    def change_focused_car(self):
        print ("Changing focused car.")
        
        if(self.config.get("cam_changer","reset_camera")=="yes"):
            print "Resetting camera to cam."
            self.cur_carcam=0
            self.ccam_t.stop()
            self.ccam_t=WorkDaemon(work_method=self.change_carcam,interval=self.config.getfloat("cam_changer", "camchange_interval"),run_once=False)
            self.ccam_t.start()
        
        self.sendMsg("/press tab",'')
        
       
    def chat_message(self,insim,mso):
        InsimClient.chat_message(self, insim, mso)
        
        if(mso.Msg.count("start_cam_changer")>0):
            self.begin()
        elif("camtest" in mso.Msg):
            self.camtest()
            
    def camtest(self):
        self.sendMsg("CAMTEST")
        self.insim.send(pyinsim.ISP_CPP,Pos=[-31373253,30219388,15*65536], Flags=pyinsim.ISS_SHIFTU,ViewPLID=41 )
    
    def race_state(self,insim, rsp):
        InsimClient.race_state(self, insim, rsp)
        try:
            p=self.config.get("cam_changer","props")
            p=[int(x) for x in p.split(",")]
            self.del_button(45, 0)
            if(self.current_driver_id>0):
                drv=self.get_driver(self.current_driver_id)
                self.send_button(45, p[1],p[0], p[2], p[3], "^7"+str(drv.position)+". "+(drv.playername.encode("latin-1")), 0, pyinsim.ISB_DARK|pyinsim.ISB_LEFT)
        except:
            print "Error sending button"
    def race_start(self,insim,rsp):
        InsimClient.race_start(self, insim, rsp)
        self.c_count=1
                
    def begin(self):
        print "Cam_Changer started."
        self.sendMsg("Cam_Changer started.")
        
        if(self.ccam_t is not None):
            self.ccam_t.stop()
        
        if(self.ccar_t is not None):
            self.ccar_t.stop()
        
        self.ccam_t=WorkDaemon(work_method=self.change_carcam,interval=self.config.getfloat("cam_changer", "camchange_interval"),run_once=False)
        self.ccar_t=WorkDaemon(work_method=self.change_focused_car,interval=self.config.getfloat("cam_changer", "carchange_interval"),run_once=False,run_first_time=False)
        self.cmsg_t=WorkDaemon(work_method=self.draw_big_button,interval=self.config.getfloat("cam_changer", "tickerchange_interval"),run_once=False)
        self.ccam_t.start()
        self.ccar_t.start()
        self.cmsg_t.start()