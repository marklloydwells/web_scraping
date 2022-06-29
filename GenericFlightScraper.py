# -*- coding: utf-8 -*-
"""
Created on Wed Jul 18 15:02:56 2018

@author: mark
"""

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait # to do
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException
import sqlite3
import logging
import re
import numpy as np

from selenium.webdriver.support import expected_conditions as EC #to do
from selenium.webdriver.common.by import By #to do

from my_logger import my_logger
from load_app_data import load_app_data
from datetime import datetime, date, timedelta




class GenericFlightScraper(object):
    def __init__(self, driver_type = 'PhantomJS'):
#    airports, depart_airports,
#                 user_agent, future_timedelta = 1,
#                 days_ahead=90, debug=False, one_way=True, return_durations=[7,14],
#                 
#                 ):
        my_logger(loglevel='info', print_to_console_level='info')
        self.count_of_successfull_loads = 0
        self.base_urls = []
        self.user_agent = None
        
#        if type(user_agent) != type('str'):
#            raise TypeError, "user_agent must be a string"
        if driver_type == 'PhantomJS':
            webdriver.DesiredCapabilities.PHANTOMJS['phantomjs.page.settings.userAgent'] = user_agent
            self.driver = webdriver.PhantomJS(r'C:\Users\mat4m_000\Downloads\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe')
        if driver_type == 'Chrome':
            self.driver = webdriver.Chrome()
            
#        if debug:
#            self.debug( driver, airports, depart_airports, 
#                 user_agent,)
#        else:
#            self.main_process(driver, airports, depart_airports, 
#                 user_agent, days_ahead, future_timedelta, return_durations)


    def main_process(self, destination_airports, depart_airports, 
                 days_ahead, future_timedelta, return_durations):
        for day_delta in xrange(3, days_ahead, 4):
            todays_date = date.today() + timedelta(future_timedelta) #so, 1 is actually tomorrows date
            logging.debug('Start date for search is {}'.format(todays_date))
            date_to_search = datetime.strftime(todays_date + timedelta(day_delta) , '%Y-%m-%d')

#            for u in self.base_urls:
            for dest_airport in destination_airports:
                for depart_airport in depart_airports:
                    if dest_airport != depart_airport:
                        ## ordinarily in operational use we should do both no?

#                        if 1: #if one_way:
#                            self.one_way(u, depart_airport, dest_airport, date_to_search, user_agent)
                        if 1: #if return_durations:
                            self.return_flight(return_durations, todays_date, day_delta,
                                               u,depart_airport, dest_airport,date_to_search,)


    
    def to_sql(self, df, table_name='Kayak_data'):
        conn = sqlite3.connect(load_app_data()+r'\flight_data.db')
        df.to_sql(table_name,conn,if_exists='append',index=False)
        conn.close()
     