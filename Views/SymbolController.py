"""
|--------------------------------------------------------------------------------------------|                                                                                            |
|        THIS CLASS IMPLEMENTS THE CRUD OPERATIONS & BUSINESS LOGIC ON SYMBOL TABLE          |                                                                                            |
|--------------------------------------------------------------------------------------------|
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from Helper.helpers import remove_dupe_dicts
from Vendors.Alpaca import Alpaca
from Vendors.OpenFigi import OpenFigi
import pandas as pd
from Models.sqa_models import Symbol

class SymbolController:
    def __init__(self):
        self.url =config.DB_URL
        self.Session =sessionmaker()
        engine =create_engine(self.url, echo = True)
        self.Session.configure(bind=engine)

    def bulkInsertFromProviders(self ,vendor_name):
        '''Fetches the list of stocks from the provider (ALPACA).generates a list of dic for the Symbol Mapper & adds records to the table
        Parameters - vendor_name : str() - A list of stock symbols that conform to the Alpaca API request structure.'''

        session =self.Session()

        alpaca =Alpaca()
        asset_list =alpaca.getAssetList()

        # returns a list of dictionary for "active" and "tradable" universe
        alpaca_dict = [{"exchange_Acr": getattr(asset, "exchange")
                           , "ticker": getattr(asset, "symbol")
                           , "name": getattr(asset, "name")} for asset in asset_list
                       if asset.status == 'active' and asset.tradable]

        unique_dict =remove_dupe_dicts(alpaca_dict)

        return (unique_dict)

    def get_lists(self ,dict):
        ticker_list = [dict[i]['ticker'] for i in range(len(dict))]
        exchange_list = [dict[i]['exchange_Acr'] for i in range(len(dict))]
        name_list = [dict[i]['name'] for i in range(len(dict))]

        return (ticker_list, exchange_list, name_list)


    #Change all this code........

    def create_dictionary(self,ticker_list, name_list):

        session = self.Session()
        openfigi = OpenFigi()
        job = [{'idType': 'TICKER', 'idValue': 'AAPL'}]
        sample = openfigi.get_figi(job)
        df = pd.DataFrame(columns=sample.columns)
        error_tickers = []

        for i in range(5):
            try:
                jobs = [{'idType': 'TICKER', 'idValue': ticker_list[i]}]
                df_figi = openfigi.get_figi(jobs)
                df_figi['name'] = name_list[i]

                df = pd.concat([df, df_figi], axis=0, ignore_index=True, sort=False)

                # print("df",df)

            except Exception as e:
                error_tickers.append(ticker_list[i])
                pass

        df['status_id'] = (df['figi'] == df['compositeFIGI'])

        # df_dict = [{"ticker": row['ticker'],"name": row['name'],"figi": row['figi']
        #             ,"exchCode": row['exchCode'],"marketSector": row['marketSector']
        #             , "securityType": row['securityType'], "securityType2": row['securityType2']
        #             , "securityDescription": row['securityDescription'], "compositeFigi": row['compositeFIGI']
        #             ,"shareClassFigi": row['shareClassFIGI']
        #             }
        #            for index, row in df.iterrows()]
        #
        # # print("df_dict",df_dict)

        # try:
        #     session=self.Session()
        #     session.bulk_insert_mappings(Symbol,df_dict)
        # except Exception as e:
        #     # raise e
        #     print(f"There was some Error inserting data Error:{e}")
        #     session.rollback()
        # finally:
        #     print("..")

        # session.commit()

        #DELETE FROM HERE - AND UNCOMMENT ABove LINES
        df_dict = [{"ticker": row['ticker'],"name": row['name'],"figi": row['figi']
                    , "compositeFigi": row['compositeFIGI'],
                    "status_id": row['status_id']
                    }
                   for index, row in df.iterrows()]

        # print("df_dict",df_dict)

        try:
            session=self.Session()
            session.bulk_insert_mappings(Symbol,df_dict)
        except Exception as e:
            # raise e
            print(f"There was some Error inserting data Error:{e}")
            session.rollback()
        finally:
            print("..")

        session.commit()