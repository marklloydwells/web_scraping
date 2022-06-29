# -*- coding: utf-8 -*-
"""
Created on Mon Jan 12 10:44:42 2015

@author: wellsm
"""

import time
import re
import win32api

from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime, time as dtime
from bs4 import BeautifulSoup

def initialise():
    fp = webdriver.FirefoxProfile()
    fp.set_preference("network.websocket.enabled", False) # to stop the proxy auth message - doesnt seem to work
    fp.set_preference('signon.autologin.proxy',True) # to stop the proxy auth message - doesnt seem to work either!
    
    fp.set_preference("network.http.phishy-userpass-length", 255);
    fp.set_preference("network.automatic-ntlm-auth.trusted-uris", "10.8.224.13");
    
    browser = webdriver.Firefox(firefox_profile=fp)
    browser.implicitly_wait(30)
    browser.set_page_load_timeout(30)
    return browser

def main(browser):
    try:
        browser.get('https://skygardentickets.com/')
        browser.find_element_by_id('btnBookNow').click()
        browser.find_element_by_id('txtPartySize').send_keys('6')
        browser.find_element_by_name('ctl00$MainContent$btnProceed').click()
        month_avaialable = browser.find_element_by_id('calDiary_X3').get_attribute('innerHTML')
        month_eq_march_bool = (month_avaialable == 'March 2015')
        print month_avaialable
        if not month_eq_march_bool:
            msg = "SkyTickets month has been updated!"
            win32api.MessageBox(0, msg , 'Alert!', 0x00001000) 
#    browser.close()
    except Exception as ex:
        print ex
    raw_input('Press any key to continue...')

if __name__ == "__main__":
    browser = initialise()
    main(browser)
       

    