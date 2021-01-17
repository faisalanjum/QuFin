import alpaca_trade_api as Api
import config as Config
import pandas as pd

"""
|--------------------------------------------------------------------------------------------|                                           |
| THIS CLASS IMPLEMENTS THE WRAPPER FOR ALPACA DATA PROVIDER IMPLEMENTED USING ALPACA API....|                                              |
|--------------------------------------------------------------------------------------------|
"""

class Alpaca:

    def __init__(self):

        # class properties
        self.key = Config.ALPACA_API_KEY
        self.secret = Config.ALPACA_SECRET_KEY
        self.url = Config.ALPACA_API_URL
        """
        ------------------------------------------------------------------------------------------------------------
                          Create connection with the alpaca server
        ------------------------------------------------------------------------------------------------------------
        """
    def connect(self):
        try:
            self.connection = Api.REST(self.key, self.secret, self.url)
            print("Connection Established With Alpaca")
        except Exception as e:
            print("Error Connecting to Provider")
            raise e
        """
        ------------------------------------------------------------------------------------------------------------
            Retreives The List Of Stocks With Their Symbols,Name and Other Details 
        ------------------------------------------------------------------------------------------------------------
        """
    def getAssetList(self):
        ''' Send a collection of stock symbols to the API in order to obtain the associated prices.
            Returns: Dict of Stocks With List'''

        self.connect()

        try:
            account_info = self.connection.get_account()
            if account_info.status == "ACTIVE":
                self.assetList = self.connection.list_assets()
                return self.assetList

        except Exception as e:
            raise e

        """
        ------------------------------------------------------------------------------------------------------------
            Get Stock_prices
        ------------------------------------------------------------------------------------------------------------
        """
    def getStockPrices(self, symbols=None, timeframe='1D', start=None, end=None, limit=None, output_as=None):
        '''
            Send an collection of stock symbols to the API in order to obtain theassociated prices.
            ----------
            Parameters
            symbol : list() - A list of stock symbols that conform to the Alpaca API request structure.
            timeframe:str - Possible values are 1D,1Min,5Min,15Min,day
            start :ISO Format datetime str()
            end :ISO Format datetime str()
            output_as:str allowed value=dataframe
            limit:Int
            timeframe:str
            Returns: DATAFRAME of stockprices
        '''

        if symbols == None:
            import Helper.helpers as Helper
            self.getAssetList()
            symbol_list = [getattr(asset, "symbol") for asset in self.assetList]
            stock_list = list(Helper.divide_chunks(symbol_list, 50))
        else:

            self.connect()
            stock_list = symbols

        try:
            if output_as == None:
                stock_prices = [
                    self.connection.get_barset(symbols, timeframe=timeframe, limit=limit, start=start, end=end) for
                    symbols in stock_list]
            else:
                stock_prices = [
                    self.connection.get_barset(symbols, timeframe=timeframe, limit=limit, start=start, end=end).df for
                    symbols in stock_list].df

            return stock_prices

        except Exception as e:
            raise e


# alpaca =Alpaca()
# asset_list =alpaca.getAssetList()
# print(asset_list)
# print(len(asset_list))

