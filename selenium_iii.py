# -*- coding: utf-8 -*-
"""
Created on Thu Oct 23 15:50:12 2014

@author: wellsm
"""

    

import threading

from selenium import webdriver
from time import sleep

def initialize():
    iiibrowser = webdriver.Firefox()
    iiibrowser.implicitly_wait(10)
    iiibrowser.get('https://trading.iii.co.uk/user/login?return=https%3A%2F%2Ftrading.iii.co.uk%2Faccount%2Ftrading%2F&trading=1')
#    intial_window_handle = iiibrowser.window_handles
    iiibrowser.find_element_by_id('login-login_username').send_keys("iamb4ne1")

#    elem=iiibrowser.find_element_by_id('login-login_password')  
    return iiibrowser

def iii_function(iiibrowser, event):
    try:
        if iiibrowser is not None:
    #        print 'Switching off the event flag'
            event.clear()
    #        print 'End of try clause'
        else:
    
            print 'Initializing iii'
            iiibrowser = initialize()
            event = threading.Event()
            t = threading.Thread(name='Selftrade_refresh_thread', 
                             target=wait_for_event,
                             args=(event,iiibrowser))
            t.start()
            sleep(20)
    #    print "Switching on the event flag"
        event.set()
        return iiibrowser, event
    except Exception as ex:
        print "In iii_function,", ex
        return iiibrowser, event   
    


def wait_for_event(event, iiibrowser):
    while event.wait():
        sleep(400)
        if event.is_set():
            iiibrowser.refresh()
            print 'iii browser refreshed'     

        
if __name__ == "__main__":

    iiibrowser = None
    event = None
    iiibrowser, event = iii_function(iiibrowser, event)
    