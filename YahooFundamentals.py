# -*- coding: utf-8 -*-
"""
Created on Sat Sep 05 15:45:38 2015

@author: mat4m_000
"""

import urllib2
import pandas as pd

from datetime import datetime
from io import StringIO

from yticker import yticker

class YahooFundamentals:
    def __init__(self, ticker):
        self.ticker = yticker(ticker)
        self.dt = datetime.today()
        url_string = "http://download.finance.yahoo.com/d/quotes.csv?s={}".format(self.ticker)
#        url_string += "&f=sl1d1t1c1hgvbap2"
        url_string += "&f=sb4c1ee7e8e9g1i5i"
#        url_string += "&g={0}".format(interval)
#        csv = urllib2.urlopen(url_string).read()
#        print csv
#        buf = StringIO(unicode(csv))
        self.df = pd.read_csv(url_string, header=None)
        self.df.columns = ['ticker','book_value', 'change', 'EPS',
            'EPS Estimate Current Year', 'EPS Estimate Next Year',
            'EPS Estimate Next Quarter', 'Holdings Gain Percent',
            'order book', 'More Info'

            ]


        
if __name__ == "__main__":
    yf = YahooFundamentals('TEF')
    print yf.df