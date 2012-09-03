from myinsim.insim_client import InsimClient
import pyinsim


class ReorderInsim(InsimClient):
    """
    Reorder Main Class
    """
    def __init__(self):
        InsimCLient.__init__(self, "Reorder")
        self.version="2.0"
        self.dlist=[]

    def send_reorder(self):
        print "Sending Reorder"
        tam=32-self.dlist.count(0)
        self.insim.send(pyinsim.ISP_REO, NumP=tam, PLID=self.dlist)

    def small(self,insim, packet):
        InsimClient.small(self,insim, packet)
        if(packet.UVal==pyinsim.SMALL_SSG):
            self.send_reorder()


    def build_grid(self):
        print "Building grid"
        self.dlist=[]#reset list
        
        for t in self.config.items("reorder_list"):
            try:
                self.dlist.append(self.get_driver_by_uname(t[1]).player_id)
            except:
                print "Driver ",t[1]," is not on track"
        
        for i in range(0, 32-len(self.dlist)):
            self.dlist.append(0)

    def hidden_message(self, insim, msg):
        InsimClient.hidden_message(self, insim, msg)
        msg=msg.Msg
        if(msg=="setgrid"):
            self.send_reorder()


