'''
Created on Feb 5, 2012

@author: jason_new
'''
from myinsim.insim_client import InsimClient,WorkDaemon
import pyinsim

class EVT(InsimClient):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        InsimClient.__init__(self, "Event_Timer")
        self.version=0.1
        self.flags=""
        self.timer_thread=None
        self.tm=0#time in seconds
        self.paused=True
        self.msg=""
        self.first=True
    def reset(self):
        pass
    
    def hidden_message(self, insim, msg):
        InsimClient.hidden_message(self, insim, msg)
        
        try:
            t=msg.Msg
            print t
            t=t.split(" ")
            print t
            cmd=t[0]
            
            if(cmd=="evtset"):
                #the last item is the time
                tm=float(t[-1:][0])*60
                m=" ".join(t[1:-1])
                print tm
                self.set_evt(tm, m)
            elif(cmd=="evtpause"):
                self.pause_evt()
            elif(cmd=="evtclear"):
                self.clear_evt()
            elif(cmd=="evtunpause"):
                self.unpause_evt()
                
        except:
            print "Command error"
            print msg.Msg
    def set_evt(self,tm,msg):
        '''
        tm time in seconds
        '''
        print "Set evt msg: ", msg, " time ",tm
        #stop thread
        if(self.timer_thread is not None):
            self.timer_thread.stop()
        
        self.msg=msg
        #create a new timer thread
        self.tm=tm
        self.timer_thread=WorkDaemon(self.draw_evt, 1, False)
        #start it
        self.first=True
        self.timer_thread.start()
        if(self.config.get("evt","send_rcm")=="yes"):
            self.sendRCM(msg)
            
    def clear_evt(self):
        if(self.timer_thread is not None):
            self.timer_thread.stop()
            
        self.del_button(125)
        self.del_button(126)
        self.first=True
        self.tm=0
        self.sendMsg("/rcc_all",'')
    def pause_evt(self):
        
        if(self.timer_thread is not None):
            self.timer_thread.pause()
    def unpause_evt(self):
        
        if(self.timer_thread is not None):
            self.timer_thread.unpause()
            
    def draw_evt(self):
        if(self.tm==-1):
            self.timer_thread.stop()
            return
        
        #2 buttons
        top=self.config.getint("evt","posy")
        left=self.config.getint("evt","posx")
        w=13
        h=9
        #format time
        u=(pyinsim.time(self.tm*1000))
        t_msg="%.2d"%(u[0]*60)+":"+"%.2d"%(u[2]) 
        cl="^3"
        if(self.tm<=59):
            cl='^1'
        t_msg=cl+t_msg
        self.send_button(125, top, left, w, h, t_msg, bs=pyinsim.ISB_DARK)
        
        if(self.first):
            w_m=60
            self.send_button(126, top, left+w, w_m, h, '^7'+self.msg, bs=pyinsim.ISB_LIGHT|pyinsim.ISB_LEFT)
        
        self.first=False
        self.tm-=1