# -*- coding: utf-8 -*-
"""
Created on Sun Jul 12 14:58:36 2015

@author: wellsm
"""
from __future__ import print_function

import urllib.request as urllib
#import execjs
import logging
import datetime as dt
import os

from bs4 import BeautifulSoup
from re import sub
from urllib.parse import urljoin

from investegate_news_scrape import RNS_types, pos_strings, neg_strings
#from setproxy import setproxy
#from DirectorDealings import DirectorDealings
from send_mail import send_mail
from DataTable import DataTable
#from DLData_object import GetTickerDLData
from YahooKeyStats import YahooKeyStats
from my_logger import my_logger
from ShareCast import ShareCastCompany, ShareCastNavigator
from load_app_data import load_app_data

def main():
    my_logger(loglevel='info')
    ins = InvestegateNewsScrape()
    ins.fetch_director_dealings()
    ins.fetch_news_articles()
    try:
        from NewsClassifier import NewsClassifier
        nc = NewsClassifier()
        nc.fit_pipeline() # should just load classifier from pickle here
#        nc.classify(ins.ticker_news_dict.items()) # passes a list
        for ticker, na in ins.ticker_news_dict.iteritems():
            if na is not None:
                na_classification = nc.classify(na)
                logging.info('{}: Classification: {}'.format(na.headline.encode('utf8'), na_classification ) )
                ins.msg += '\nTicker: {}, {}: Classification: {}, url: {}'.format(
                    na.ticker, na.headline.encode('utf8'), na_classification, na.url )
            else:
                logging.warning('na is none for {}'.format(ticker))
    except:
        logging.exception('')
    ins.save_to_file()
    ins.send_mail()
    input("Press enter to continue...")
    return ins # in case further investigation is required

def basic_run():
    my_logger(loglevel='debug')
    
    date=None
    
    ins = InvestegateNewsScrape(date=date)

    ins.fetch_news_articles()
    ins.save_to_file(open_file=True)
    #ins.send_mail()
    return ins


def historic_run(date):
    my_logger(loglevel='debug',) # print_to_console_level='debug')
    logging.debug(f'Initialising historic INS with date {date}')
    ins = InvestegateNewsScrape(date=date)
    ins.fetch_news_articles()
    ins.save_to_file(open_file=True)
    return ins

def debug():
    pass
    


class InvestegateNewsScrape(object):

    def __init__(self, date=None):
        """

        Parameters
        ----------
        date : TYPE, optional
            DESCRIPTION. format yyyymmdd The default is None.

        """
        logging.info('Initialising InvestegateNewsScrape')
        #setproxy()
        self.newspage = r'http://www.investegate.co.uk/Index.aspx?limit=-1'
        self.date = date
        if date is not None:
            self.newspage += f'&date={date}'  # 
        self.root = r'http://www.investegate.co.uk/'
        self.first_day_strings= ['first day', 'Intention to Float', 'intention to list', 'Pricing of Initial Public Offering']
        self.url_list = []
        self.msg = 'InvestegateNewsScrape:\n\n'
        self.ticker_news_dict = {}
        self.fetch_headlines()
        self.dd = None
        self.scn = ShareCastNavigator()
        
    def fetch_headlines(self):
        logging.debug(f'Fetching headlines from {self.newspage}')
        try:
            request = urllib.Request(self.newspage, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",})
            html = urllib.urlopen(request).read()
        except urllib.HTTPError:
            logging.exception(self.newspage)
            self.__init__()
            return
        soup = BeautifulSoup(html, features='lxml')
        table_soup = soup.find('table',{'id':'announcementList'})
        headers = ['time', 'RNS', 'None1', 'None2', 'Company', 'Announcement', 'None3', 'None4', 'None5']
        self.df = DataTable(table_soup,headers=headers, ).to_dataframe(hrefs=True)

        for index, row in self.df.iterrows():
            headline = row['Announcement'] 
            for rns_type in RNS_types():
                if headline is not None and rns_type.upper() in headline.upper():
                    ##get ticker from href
                    logging.info("Headline found: {}".format(headline.encode('utf-8')))
                    newspage_ticker = sub('[()]', '', row['Company'].split()[-1])
                    self.ticker_news_dict[newspage_ticker] = None
                    
    def fetch_director_dealings(self):
        logging.debug('Fetching news articles')
        try:
            self.scc.get_director_dealings()
        except:
            logging.exception('')
            self.dd = None


                    
    def fetch_news_articles(self):
        for index, row in self.df.iterrows():
            headline = row['Announcement']
            #logging.debug('headline object type is: {}'.format(type(headline)))
            if headline is not None:
                headline = headline.encode('utf8')
            for rns_type in RNS_types():
                ## Check whether the headline is one that we are interested in
                if headline is not None:
                    if headline and rns_type.upper() in str(headline.upper()):
                        logging.info("Getting news for headline: {}".format(headline))
                        newspage_ticker = sub('[()]', '', row['Company'].split()[-1])
                        ## follow link and get news text
                        na = NewsArticle(urljoin(self.newspage,row['href_Announcement']), self.scn,  headline)
                        if na.ticker != newspage_ticker:
                            logging.warning('na.ticker != newspage_ticker. na: {}, newspage: {}, url: {}'.format(na.ticker, newspage_ticker, na.url))
    
                        else:
                            self.ticker_news_dict[newspage_ticker] = na
                        if na.is_significant:
                            if self.dd is not None:
                                na.msg += "Director dealings: {}\n".format(self.dd.get_ticker_dealings(na.ticker))
                        self.msg += na.msg
                        # end if
                    # end if
                # end if
            # end for   
            for first_day_string in self.first_day_strings:
                if headline is not None and str(first_day_string.upper()) in str(headline.upper()):
                    msg1 = '\n************************************************\n{} found in {}{}\n'.format(first_day_string.upper(), 
                                                self.root , row['href_Announcement'] )
                    print(msg1)
                    logging.info(msg1)
                    self.msg += msg1

                    
    def send_mail(self):
        logging.debug('Sending mail')
        send_mail(self.msg, 'Investegate News Scrape')


    def print_to_log(self):
        logging.info(self.msg)


    def save_to_file(self, filepath=None, open_file=False):
        if filepath is None:
            if self.date is None:
                #filepath = config.main_path+r'\InvestegateNews_{}.txt'.format(dt.date.today())
                filepath = load_app_data()+r'\InvestegateNews\InvestegateNews_{}.txt'.format(dt.date.today())
            else:
                #filepath = config.main_path+r'\InvestegateNews_{}.txt'.format(self.date)
                filepath = load_app_data()+r'\InvestegateNews\InvestegateNews_{}.txt'.format(self.date)

        self.output_file = filepath
        with open(filepath, 'w', encoding="utf-8") as f:
            f.write(self.msg)
        if open_file:
            os.system('start "" "{}"'.format(filepath))
        
    def save_to_sqlite(self,filepath=None):
        """ For future analysis, save the word(s) found and the ticker and date"""
        raise NotImplementedError
        
class NewsArticle(object):
    positive_string_list = pos_strings()
    neg_string_list = neg_strings()

    def __init__(self, url, scn, headline=''):
        try:
            headline = str(headline).encode('utf-8')
            logging.debug('Initialising news article: {}'.format(headline))
        except UnicodeDecodeError:
            logging.exception(url)
            headline = '!!!!!!!'
        self.url = url
        self.headline=str(headline).encode('utf8')
        self.msg = ''
        self.ticker = ''
        self.div_string = ''
        self.is_significant = False
        self.scn = scn


        self.retrieve_article()
        
    ## to do: more descriptive name and description for this fuction:
    def retrieve_article(self):
        try:
            request = urllib.Request(self.url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0",})
            html = urllib.urlopen(request).read()
            soup = BeautifulSoup(html, features="lxml")
            if soup.find("div", {"id":"ArticleContent"}):
                self.div_string = div_string = soup.find(
                        "div", {"id":"ArticleContent"}
                        ).get_text().encode('utf8', 'ignore')
            else:
                logging.warning('No article content found for '+str(self.url))
                self.div_string = div_string = ''
                
            if soup.find("h1"): # check that there is a ticker on the page
                co_name = str(soup.find("h1")(text=True)[0])
                logging.debug('Company name found on NA page: {}'.format(co_name.encode('utf8','ignore')))
                self.ticker = sub(r'[()]','',co_name.split()[-1])
                logging.debug('Ticker found: {}'.format(self.ticker))
                self.msg += self.string_finder(self.positive_string_list,div_string)
                self.msg += self.string_finder(self.neg_string_list,div_string)
            else:
                logging.warning('No ticker found for '+str(self.url))
        except urllib.URLError:
            print(str(self.url))
        except:
            logging.exception(self.url)
            
    def string_finder(self,strings_to_find_list, div_string):
        msg = ''
        for str_ in strings_to_find_list:
            try:
                str_ = str_.upper() #str(str_).upper()
                div_string = str(div_string)
                logging.debug(type(str_))
                logging.debug(type(div_string))

                ## always <str>
                #logging.debug('object type of str_ is {}'.format(type(str_)))
                if str_ in div_string.upper():
                    self.is_significant = True
                    logging.debug('{} found in NA ticker {}'.format(str_,self.ticker))
                    # position of the string to find in the text
                    ## DOESNT SEEM TO BE WORKING 
                    pos = div_string.upper().find(str_) 
                    logging.debug('position in text: {}'.format(pos))
                    logging.debug(type(pos))
                    logging.debug(div_string[pos-10:pos+10])

                    paragraph = div_string[pos-170:pos+170]
                    msg += self.create_msg(str_, paragraph, )
                    msg += '\n'
                else:
                    pass
            except Exception:
                logging.exception('str_ type: {}, beautifulsoup type: {}'.format(type(str_), type(self.div_string.upper())))
        if not self.is_significant:
            logging.debug('No important strings found in NA {}'.format(self.ticker))
        return msg
        
    def create_msg(self, found_string, paragraph,):
        scc = self.fetch_fundamental_data()
        try:
            fundamentals = scc.fundamentals
            forecasts = scc.forecasts
        except AttributeError:
            logging.warning('Sharecast info not available for {}'.format(self.ticker))

        
        msg = '\n********************************************'
        msg += "\n%s found in %s\n" % (found_string, self.url)
        logging.info("%s found in %s" % (found_string, self.url))
        msg += '"'+paragraph+'"\n'
        msg += "https://uk.finance.yahoo.com/q/bc?s={0}.L\n".format(self.ticker)
        msg += "http://uk.advfn.com/p.php?pid=news&symbol={0}\n".format(self.ticker) 
        try:
            msg += 'Market Cap: {}\n'.format(scc.market_cap_text)
            msg += 'Pre-tax forecast: {}\n'.format(scc.pre_tax_forecast)

            msg += fundamentals.to_string()
            msg += '\n'
            msg += forecasts.to_string()
            msg += '\n'
            for dd_item in scc.dd_list:
                msg += dd_item.to_string()
                msg += '\n'
                
        except:
            logging.info('No fundamentals or forecasts available for {}'.format(self.ticker))
#        if v is not None:
#            try:
#                if tdld.PEG is not None: # v[column_names.index('PEG')] is not None:
#                    msg += tdld.callable_DL_print() #.encode('utf-8', 'ignore')
#            except:
#                logging.exception('')
#        else:
#            msg+= "No DL data \n"
        return msg


    def fetch_fundamental_data(self,):
        try:
            yks = YahooKeyStats(self.ticker)
            yks.from_yahoo()
            yks.to_sqlite()
        except:
            logging.exception('')
        #tdld = GetTickerDLData(self.ticker) # GetTickerDLData class automatically saves to sqlite
        try:
            scc = ShareCastCompany(self.scn, ticker=self.ticker)
            scc.main_page_data()
            scc.write_df_to_sql(scc.fundamentals, 'fundamentals')
            scc.get_director_dealings()
            return scc
        except:
            logging.exception('')
            return None

    def summarize(self, num_sentences=4):
        from summarize import SimpleSummarizer
        print(SimpleSummarizer().summarize(self.div_string.decode('utf8','ignore'), num_sentences ))

    def __repr__(self):
        return self.div_string

if __name__ == "__main__":
    pass
    ins = basic_run()

#newspage = r'http://www.investegate.co.uk/Index.aspx?limit=-1'
#rns_types = RNS_types()
#html = urllib2.urlopen(newspage).read()
#soup = BeautifulSoup(html)
#for link in soup.findAll(href=True):
#    for rns_type in rns_types:
#        if link.text is not None and rns_type.upper() in link.text.upper():
#            print link['href'], rns_type.upper(), link.text.upper()
#            print rns_type.upper() in link.text.upper()