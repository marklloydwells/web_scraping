# -*- coding: utf-8 -*-
"""
Created on Mon Sep 07 19:12:15 2015

@author: mat4m_000
"""

try:
    import urllib2
except:
    import urllib.request as urllib2
import pandas as pd
import re
import logging
import sqlite3
import numpy as np

from bs4 import BeautifulSoup
from time import sleep
from datetime import datetime

from yticker import yticker
from get_dl_data import create_useful_dl_data_dict
from my_logger import my_logger
from load_app_data import load_app_data

def get_unit(ustr):
    if ustr == '': return 'u'
    return ustr.lower()

def parse_string(in_string):
    try:
        units={'k':10**3,'m':10**6,'g':10**9,'b':10**9,'u':1}
        r=re.compile('([0-9\.-]*)([kKmMbBgG]?)')
        result=r.match(in_string)
        return float(re.sub(r'[^0-9.-]','',in_string))*units[get_unit(result.group(2))]
    except: # Exception as e:
        #print e, in_string
        return None
        
def parse_yahoo_key_stats(ticker, filepath=None):
    if filepath is None:
        yticker_ = yticker(ticker)
        url = "https://uk.finance.yahoo.com/quote/{}/key-statistics?ltr=1".format(yticker_)      
        try:
            html = urllib2.urlopen(url).read()
        except urllib2.HTTPError:
            logging.exception(url)
    else:
        with open(filepath, 'rb') as f:
            html = f.read()
    soup=BeautifulSoup(html, 'lxml')
    data_dict={}
    for t in soup.find_all('td',{'class':'yfnc_tablehead1'}):
        header = t(text=True)[0].split('(')[0].rstrip(u' :\xb3')
        if header == 'Avg Vol':
            header = 'Average Volume'
        data_dict[header] = parse_string(t.find_next_sibling().string)
    s = pd.Series(data_dict,)
    return s

def crawl_all_key_stats():
    df_dict = {}
    my_logger()
    for ticker, dldata in create_useful_dl_data_dict(return_columns=False).iteritems():
        try:
            df_dict[ticker] = parse_yahoo_key_stats(ticker)
            logging.info('Successfully recorded the key stats for {}'.format(ticker))
            sleep(1)
        except:
            logging.exception('')
    df = pd.DataFrame.from_dict(df_dict, orient='index')
    df['read_date'] = datetime.today()   
    dbpath = load_app_data() + r'\\keystats_test.db'
    conn = sqlite3.connect(dbpath)
    df.to_sql('keystats', conn)
    conn.close()
    
    
class YahooKeyStats:
    def __init__(self, ticker):
        self.ticker = ticker
        self.db_filepath = load_app_data() + r'\\Yahookeystats.db'
        
        
    def from_yahoo(self):
        data_dict = {self.ticker:parse_yahoo_key_stats(self.ticker)}
        self.df = pd.DataFrame.from_dict(data_dict, orient='index', )
        self.df['read_date'] = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return self.df
        
    def from_file(self, filepath, date_stamp):
        data_dict = {self.ticker:parse_yahoo_key_stats(self.ticker, filepath)}
        self.df = pd.DataFrame.from_dict(data_dict, orient='index', )
        self.df['read_date'] = date_stamp
        return self.df
        
    def from_sqlite(self):
        conn = sqlite3.connect(self.db_filepath)
        try:
            sql = "select * from keystats where [index] = '{}'".format(self.ticker)
            self.df = df = pd.read_sql(sql, conn,) #index='ticker')
            return df
        except:
            logging.exception(sql)
        finally:
            conn.close()
            
    def net_debt(self):
        try:
            return (self.df['Total Debt'] - self.df['Total Cash']).values[0]
        except:
            logging.exception('')
            return np.nan
        
    def to_sqlite(self,):
        conn = sqlite3.connect(self.db_filepath)
        try:
            self.df.to_sql('keystats', conn, if_exists='append')
        except:
            logging.exception(self.df)
        finally:
            conn.close()

if __name__ == "__main__":
    from setproxy import setproxy
    setproxy()
    yks = YahooKeyStats('MTEC')
#    yks.from_yahoo()
#    yks.to_sqlite()
#    crawl_all_key_stats()
    yks.from_sqlite()