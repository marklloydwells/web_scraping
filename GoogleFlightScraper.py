# -*- coding: utf-8 -*-
"""
Created on Fri Sep 07 18:41:25 2018

@author: mark
"""


import logging
import pandas as pd

from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from time import sleep

from GenericFlightScraper import GenericFlightScraper
from to_temp_file import to_temp_file, read_from_tempfile

## Google flights
""" https://www.google.com/flights/#flt=SFO.LON.2018-09-06*LON.SFO.2018-09-10;c:USD;e:1;s:1*1;md:540*540;sd:1;t:f """

## single price
"""//*[@id="flt-app"]/div[2]/main[2]/div[9]/div[1]/div[2]/div[2]/div/div[3]/div/div[3]/div/div[2]/div[1]/span"""

def main():
    gfs = GoogleFlightScraper(driver_type='Chrome')
#    url = gfs.make_return_url('LTN','IEV','2018-10-06', '2018-11-06')
    origin_airports = ['LTN',
                       'STN',
                       'LGW',
                       ]
    destination_airports = ['IEV',
                            'KBP',
                            'PRG',]
    gfs.ouh = gfs.search_return_flights(origin_airports, destination_airports, max_days_ahead=4)
    return gfs

class GoogleFlightScraper(GenericFlightScraper):
       
    def search_return_flights(self, origin_airports, destination_airports,
                 max_days_ahead=90, future_timedelta=1, return_durations=[4,7,14],
                 weekend_trip=False
                 ):
        earliest_depart_date = date.today() + timedelta(future_timedelta) #so, 1 is actually tomorrows date
        logging.info('Start date for search is {}'.format(earliest_depart_date))
        ouh_error_flag = False
        while not ouh_error_flag:

            for depart_airport in origin_airports:
                for dest_airport in destination_airports:
                    if dest_airport != depart_airport:
                        for day_delta in xrange(3, max_days_ahead, 4):
                            depart_date = earliest_depart_date + timedelta(day_delta)
                            ouh_error_flag = self.return_flight(return_durations, depart_airport, dest_airport, depart_date,)
            break
        return ouh_error_flag
                        
    
    def return_flight(self, durations, depart_airport, dest_airport, depart_date,):
        for duration in durations:
            ret_date = depart_date + timedelta(duration)
            ret_url = self.make_return_url(depart_airport, dest_airport, depart_date, ret_date)
            ouh = None #fudge
            try:
                ouh = OneUrlHandler(self, ret_url)
                ouh.execute()
            except:
                logging.exception('')
                return ouh
        return False

    
    def make_return_url(self, origin_airport, destination_airport, depart_date, return_date, currency='GBP', num_changes=0):
        url = """ https://www.google.com/flights/#flt={0}.{1}.{2}*{1}.{0}.{3};c:{4};e:1;s:{5};sd:1;t:f """.format(
                origin_airport,     #must be airport code not region eg LHR not LON
                destination_airport,    
                depart_date, # example: 2018-09-06
                return_date,
                currency,
                num_changes,
                )
        logging.info('URL created: {}'.format(url))
        return url

            
class OneUrlHandler(object):
    def __init__(self, scraper, url):
        self.driver = scraper.driver
        self.url = url
        
    def execute(self):
        driver = self.driver
        driver.get(self.url)
        ## TO DO: Work out how to open the 'dates' tab, ideally with JS
        dates_xpath = '//*[@id="flt-app"]/div[2]/main[2]/div[9]/div[1]/div[2]/div[2]/div/div[3]/div/div[4]'
        dates_xpath = '//*[@id="flt-app"]/div[2]/main[2]/div[9]/div[1]/div[2]/div[2]/div/div[3]/div/div[5]/div/div[2]/div[2]'
#        dates_xpath = '//div[text()="SEE MORE"]'
        try:
            driver.find_element_by_xpath(dates_xpath).click()
        except:
            pass
            #logging.exception('')
        sleep(1)
        price_table_xpath='//*[@id="flt-flight-insights"]/div[2]/div[1]/div/div[3]'
        html = driver.find_element_by_xpath(price_table_xpath).get_attribute('innerHTML')
        soup = self.soup = BeautifulSoup(html)
        to_temp_file(soup.prettify())
        example_of_a_flight_price_xpath = '//*[@id="flt-flight-insights"]/div[2]/div[1]/div/div[3]/price-grid/div[1]/div[1]/div[3]/div'
        soup_prices_try1 = soup.find_all('div',id='flt-flight-insights')
        soup_prices_try2 = soup.find_all('div',{'class':"price-grid-cheap"})
        logging.info('soup_prices_try1: {}'.format( soup_prices_try1))
        logging.info('soup_prices_try2: {}'.format( soup_prices_try2))
        
        html = '<div data-col="1" data-row="5" class="">£162</div>'
        xpath = '//*[@id="flt-flight-insights"]/div[2]/div[1]/div/div[3]/price-grid/div[1]/div[1]/div[2]/div'
        xpath = "//div[text()[contains(.,'£')]]"
        price_elements = self.driver.find_elements_by_xpath(xpath)
        
        ## prices
        prices_list = []
        """example_of_a_price = '<div data-col="1" data-row="15" class="price-grid-cheap">£75</div>'"""
        for element in price_elements:
            print element.get_attribute('outerHTML') #innerhtml gives just the price
            soup = BeautifulSoup(element.get_attribute('outerHTML'))
            div = soup.find('div')
            if div is not None:
                try:
                    col = div['data-col']
                    row = div['data-row']
                    price = element.text
                    prices_list += (row,col,price)
                except KeyError:
                    pass
        print prices_dict
        
        page_soup = BeautifulSoup(driver.page_source)
        pg = page_soup.find_all('price-grid')
        pg[0].find_all('div',{'class':'price-grid-cheap'})
        price_list = [tag for tag in pg[0].find_all('div') if tag.has_attr('data-col') ]
        prices_list = []
        for price_soup in price_list:
            col = None
            row = None
            price = None
            print price_soup
            if 1:#price_soup is not None:
                try:
                    col = price_soup['data-col']
                    row = price_soup['data-row']
                    price = price_soup.string
                    prices_list += [(row, col, price)]
                except KeyError:
                    logging.exception('')
        print prices_list
        df = pd.DataFrame(data=prices_list)
        min_row = df[0].min()
        max_row = df[0].max()
        min_col = df[1].min()
        max_col = df[1].max()
        prices_df = pd.DataFrame(data=None,index=range(min_row,max_row)
                                ,columns = range(min_col,max_col))
        
        ## min(row) is the first depart date, min(col) is the first return date
        
        
        
        
        ## dates
        depart_dates_xpath = '//*[@id="flt-flight-insights"]/div[2]/div[1]/div/div[3]/price-grid/div[1]/div[2]/div[2]/div'
        depart_dates_selector = "#flt-flight-insights > div.gws-flights-dialog__contents > div:nth-child(1) > div > div.gws-flights-pricefinder__price-grid-container > price-grid > div.tSjb9yj4lbb__scrollable-grid.v3QEjzHx7cS__scrollable-grid.gws-flights__outline-focus > div.v3QEjzHx7cS__col-headers.v3QEjzHx7cS__fill-width > div:nth-child(2) > div"
        depart_dates_html = '<div><span style="text-transform: uppercase">Fri</span><br>28 Sep</div>'
        return_dates_xpath = '//*[@id="flt-flight-insights"]/div[2]/div[1]/div/div[3]/price-grid/div[1]/div[3]/div[2]/div'
        return_dates_selector = "#flt-flight-insights > div.gws-flights-dialog__contents > div:nth-child(1) > div > div.gws-flights-pricefinder__price-grid-container > price-grid > div.tSjb9yj4lbb__scrollable-grid.v3QEjzHx7cS__scrollable-grid.gws-flights__outline-focus > div.v3QEjzHx7cS__row-headers.v3QEjzHx7cS__fill-height > div:nth-child(2) > div"
        return_dates_html = '<div><span style="text-transform: uppercase">Tue</span><br>2 Oct</div>'
        
        depart_dates_html = driver.find_element_by_css_selector('div.v3QEjzHx7cS__col-headers.v3QEjzHx7cS__fill-width').get_attribute('innerHTML')        
        return_dates_html = driver.find_element_by_css_selector('div.v3QEjzHx7cS__row-headers.v3QEjzHx7cS__fill-height').get_attribute('innerHTML')   
        depart_dates_soup = BeautifulSoup(depart_dates_html)
        depart_dates = depart_dates_soup.text
        print depart_dates
        
        sleep(5)

def html_to_dataframe(html, df):
    soup = BeautifulSoup(html)
    col = soup.find('div')['data-col']
    row = soup.find('div')['data-row']
#    df[]
        
       
if __name__ == "__main__":
    gfs = main()