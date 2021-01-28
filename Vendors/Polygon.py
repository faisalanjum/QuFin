import alpaca_trade_api as Api
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config as Config
import pandas as pd
import requests, time, math
import threading


class Polygon:

    def __init__(self):

        self.key = Config.API_KEY_SETH
        self.secret = Config.SECRET_KEY_SETH
        self.url = Config.API_URL_SETH
        self.DATA = []
        self.TICKERDATA = []

    def connect(self):
        try:
            self.connection = Api.REST(self.key, self.secret, self.url)
            print("Connection established With Alpaca-Polygon")
        except Exception as e:
            print("Error Connecting to Alpaca-Polygon")
            raise e

    # function generates the list of url's
    def generate_url(self, symbolList):
        """ This function creates a list of urls Parameters:
        symbolList(list): list of tickers
        Returns: url(list) a list of url's """
        return [Config.POLYGON_TICKER_DETAILS.format(symbol, self.key) for symbol in symbolList]

    # function divides any list into list of chunks
    def divide_chunks(self, lst, nbr_of_itms):
        """ This function divides a list into a chuncked list of lists
        Parameters: lst(list): list of items
        nbr_of_itms(Int): the integer value that defines the total number of items in each list within the list
        Returns: list of list """
        for i in range(0, len(lst), nbr_of_itms):
            yield lst[i:i + nbr_of_itms]

    # function takes urls as an argument requests the data
    def reqest_data(self, urls):
        """ This function retrieves ticker details and adds them to global variable DATA
        Parameters: urls (list): list of url strings
        Returns: None """
        session = requests.Session()
        for url in urls:
            data = session.get(url)
            if data:
                self.DATA.append(data.json())

    # this is a threaded function that  creates multiple threads for our funciton
    def details(self, symbols):
        """This function implements threading to  retrieves the details of the ticker using the function reqest_data
        Parameters:symbols(list): list of tickers
        Returns:None"""
        urls = self.generate_url(symbols)
        """second argument to the divide_chunks function can be altered it means i want 10 items in one list we need to increase it to limit the
        threads when working with large lists"""
        chunked_url = list(self.divide_chunks(urls, 10))
        processes = [threading.Thread(target=self.reqest_data, args=(urls,), daemon=True) for urls in chunked_url]
        start = [process.start() for process in processes]
        for p in processes:
            p.join()

        return self.DATA

    # These 2 Functions Fetch All Tickers from Polygon Database
    def get_tickers(self, urls):
        session = requests.session()
        for url in urls:
            data = session.get(url).json()
            self.TICKERDATA.append(pd.DataFrame(data['tickers']))

    def get_tickers_threads(self, url=Config.POLYGON_TICKERS_URL):
        session = requests.Session()
        int_url = Config.POLYGON_TICKERS_URL.format(1, Config.API_KEY_SETH)
        data = session.get(int_url).json()
        self.TICKERDATA.append(pd.DataFrame(data["tickers"]))
        pages = math.ceil(int(data['count']) / int(data['perPage']))

        # urls = [Config.POLYGON_TICKERS_URL.format(page, Config.API_KEY_SETH) for page in range(2, 50)]
        urls = [Config.POLYGON_TICKERS_URL.format(page, Config.API_KEY_SETH) for page in range(2, pages)]

        chunked_url = list(self.divide_chunks(urls, 10))
        processes = [threading.Thread(target=self.get_tickers, args=(urls,), daemon=True) for urls in chunked_url]
        start = [process.start() for process in processes]

        for q in processes:
            q.join()

        return self.TICKERDATA

