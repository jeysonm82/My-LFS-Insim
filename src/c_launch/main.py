'''
Created on Nov 28, 2011
Custom launcher. Creates a custom semaphore indicator to control custom race starts
@author: jason_new 

'''
from custom_launcher import Custom_Launcher


a=Custom_Launcher()
a.connect()
a.init_tracker()
a.run(True)