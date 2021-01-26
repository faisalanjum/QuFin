from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Helper.helpers import remove_dupe_dicts, chunker
from Vendors.Alpaca import Alpaca
from Vendors.Polygon import Polygon
from Vendors.OpenFigi import OpenFigi
from Models.sqa_models import Symbol, VendorSymbol, Company
import config, collections, time
import pandas as pd
import numpy as np

class SymbolController():
    def __init__(self):
        self.url =config.DB_URL
        self.Session =sessionmaker()
        engine =create_engine(self.url, echo = True)
        self.Session.configure(bind=engine)
        self.DATA = []
        self.TICKERDATA = []

    def PopulateSymbol(self,vendor): #Function to decide which function to run based on Vendor
        function = getattr(self,str(vendor), lambda: "Invalid Vendor")
        return function()

    def Alpaca(self):
        alpaca =Alpaca()
        asset_list =alpaca.getAssetList()

        # returns a list of dictionary for "active" and "tradable" universe
        alpaca_dict = {getattr(asset, "symbol"): [getattr(asset, "exchange"), getattr(asset, "name")
            ,getattr(asset ,"id")]
                       for asset in asset_list if asset.status == 'active' and asset.tradable}
        ticker_list = sorted(list(alpaca_dict.keys()), key=str.upper)

        openfigi = OpenFigi()
        start_time = time.time()
        df = pd.DataFrame()
        just_dictionaries = []
        step_size = 100
        country = 'US'

        for group in chunker(ticker_list, step_size):
            jobs = [{'idType': 'TICKER', 'idValue': group[i]} for i in range(len(group))]
            job_results = openfigi.map_jobs(jobs)
            just_dictionaries = [d.get('data') for d in job_results]
            just_dictionaries = [x for x in just_dictionaries if x is not None] #remove None

            for i in range(len(just_dictionaries)):
                df_figi = (pd.DataFrame.from_dict(just_dictionaries[i]))
                df_figi['name1'] = alpaca_dict[df_figi['ticker'].values[0]][1]     #alpaca name
                df_figi['exchange1'] = alpaca_dict[df_figi['ticker'].values[0]][0] #alpaca exchange
                df_figi['id'] = alpaca_dict[df_figi['ticker'].values[0]][2]  # alpaca's id

                df_figi = df_figi.loc[(df_figi['compositeFIGI'] == df_figi['figi']) & (df_figi['exchCode'] == country)]
                df = pd.concat([df, df_figi], axis=0, ignore_index=True)

        df['internal_code'] = [1 if (row['figi'] == row['compositeFIGI']) else 0 for index, row in df.iterrows()]

        df_dict = [{"uniqueID": row['figi'],"ticker": row['ticker'],
                "name": row['name'],"compositeFigi": row['compositeFIGI'],
                "shareClassFigi": row['shareClassFIGI'],"exchCode": row['exchCode'],
                "securityType": row['securityType'], "securityType2": row['securityType2'],
                "marketSector": row['marketSector'],
                "internal_code": row['internal_code']
                }for index, row in df.iterrows()]

        # For VendorSymbol Table
        df_dict_vendorsymbol = [{"uniqueID": row['figi'],"vendor_symbol": row['id'],
                "vendor_id": 1
                }for index, row in df.iterrows()]

        #Check if tickers are "Stocks" - Can change these later
        stock_type_list = ["ETP", "ADR", "Common Stock", "REIT", "MLP", "Closed-End Fund", "NY Reg Shrs", "Unit",
                           "Right", "Tracking Stk", "Ltd Part", "Royalty Trst"]
        df_stock = df.loc[(df['securityType'].isin(stock_type_list))]

        # For Company Table
        df_dict_company = [{"name": row['name'],"ticker": row['ticker'],
                            "sector": row['marketSector'],
                            "description": row['securityDescription'],
                            "compositeFigi": row['compositeFIGI']
                                }for index, row in df_stock.iterrows()]
        # Send rest of Tickers to Forex, Indices, Crypto etc.

        try:
            session=self.Session()
            session.bulk_insert_mappings(Symbol,df_dict)
            session.bulk_insert_mappings(VendorSymbol, df_dict_vendorsymbol)
            session.bulk_insert_mappings(Company, df_dict_company)

        except Exception as e:
            print(f"There was an Error inserting data. Error:{e}")
            session.rollback()
        finally:
            print("..")
            print("Alpaca's tickers:",len(df_dict))

        session.commit()
        print("--- End of Alpaca %s Minutes ---" % ((time.time() - start_time) / 60))


    def Polygon(self):

        print("I am in Polygon")
        polygon = Polygon()

        start_time = time.time()
        df=polygon.get_tickers_threads()
        print("--- TICKERDATA %s Minutes ---" % ((time.time() - start_time) / 60))

        df = pd.concat(df, ignore_index=True, sort=True).set_index('ticker')

        # Converts code dictionary into columns
        list_codes = ['cik', 'figiuid', 'scfigi', 'cfigi', 'figi']
        for code in list_codes:
            df.loc[df['codes'].notnull(), code] = df.loc[df['codes'].notnull(), 'codes'].apply(lambda x: x.get(code))

        symbols = list(df.index.values)

        start_time = time.time()

        #Function to fetch Ticker Details from Polygon
        tickerdata = polygon.details(symbols)

        # #CHECK IF ALL TICKERS ARE BEING LOADED
        ticker_detail_df = pd.DataFrame.from_dict(tickerdata).set_index('symbol')
        print("---ticker_detail_df (DATA) %s Minutes ---" % ((time.time() - start_time) / 60))

        # Postfix "_d" to column names of "ticker_detail_df"
        new_column_names = [n + "_d" for n in list(ticker_detail_df.columns)]
        ticker_detail_df.columns = new_column_names

        # Combine both dfs - (1) Tickers(df) & (2) Ticker_Detail(ticker_detail_df)
        final_df = pd.concat([df, ticker_detail_df], axis=1,join='outer',sort =False).rename_axis('ticker')

        # Seperate final_df into 2: One with Figi's and other without
        final_df_wo_figi = final_df.copy()
        final_df_wo_figi = final_df_wo_figi[pd.isnull(final_df_wo_figi['figi'])]
        final_df_w_figi = final_df[pd.notnull(final_df['figi'])]
        final_df_w_figi.reset_index(level=0, inplace=True)
        final_df_w_figi = final_df_w_figi.set_index('figi')

        ticks_wo_figi = list(final_df_wo_figi.index.values)

        #This code is repeated (in Alpaca Function above) - make only one function
        openfigi = OpenFigi()
        just_dictionaries = []
        df1 = pd.DataFrame()
        step_size = 100
        country = 'US'

        for group in chunker(ticks_wo_figi, step_size):
            jobs = [{'idType': 'TICKER', 'idValue': group[i]} for i in range(len(group))]
            job_results = openfigi.map_jobs(jobs)
            just_dictionaries = [d.get('data') for d in job_results]
            just_dictionaries = [x for x in just_dictionaries if x is not None]
            #     ticker_list = [x for x in ticker_list if just_dictionaries is not None]

            for i in range(len(just_dictionaries)):
                df_figi = (pd.DataFrame.from_dict(just_dictionaries[i]))
                df_figi = df_figi.loc[(df_figi['compositeFIGI'] == df_figi['figi']) & (df_figi['exchCode'] == country)]
                df1 = pd.concat([df1, df_figi], axis=0, ignore_index=True)

        df1.set_index('ticker', inplace=True)

        Outer_join = pd.merge(final_df_wo_figi,df1,on='ticker',how='outer')
        Outer_join = Outer_join[pd.notnull(Outer_join['figi_y'])]
        Outer_join.reset_index(level=0, inplace=True)
        Outer_join = Outer_join.set_index('figi_y')

        # drop & rename columns
        Outer_join['cfigi'] = Outer_join['compositeFIGI']
        Outer_join.drop(['name_y', 'figi_x', 'compositeFIGI', 'exchCode',
                         'marketSector', 'securityDescription', 'securityType',
                         'securityType2', 'shareClassFIGI', 'uniqueID', 'uniqueIDFutOpt'], axis=1, inplace=True)
        Outer_join.rename(columns={'name_x': 'name'}, inplace=True)
        Outer_join.index.name = final_df_w_figi.index.name

        final_polygon = pd.concat([final_df_w_figi, Outer_join])

        # print(final_polygon)

        # drop & rename columns
        final_polygon['figi'] = final_polygon.index
        final_polygon.rename(columns={'cfigi': 'compositeFigi'}, inplace=True)
        final_polygon.rename(columns={'scfigi': 'shareClassFigi'}, inplace=True)

        # fill these later using openfigi
        final_polygon['securityType2'] = ''
        final_polygon['securityDescription'] = None
        final_polygon['exchCode'] = None
        final_polygon['name1'] = None
        final_polygon['exchange1'] = None
        final_polygon['name2'] = None

        final_polygon['status_id'] = (final_polygon['compositeFigi'] == final_polygon['figi'])

        # create new columns - similar & tags
        final_polygon.rename(columns={'sector_d': 'marketSector'}, inplace=True)
        final_polygon.rename(columns={'type_d': 'securityType'}, inplace=True)
        final_polygon.rename(columns={'country_d': 'country'}, inplace=True)
        final_polygon.rename(columns={'exchangeSymbol_d': 'exSymbol'}, inplace=True)
        final_polygon.rename(columns={'similar_d': 'similar'}, inplace=True)
        final_polygon.rename(columns={'tags_d': 'tags'}, inplace=True)

        final_polygon2 = final_polygon.copy()

        col = ['figi', 'ticker', "name", "compositeFigi", "shareClassFigi", "exchCode", "marketSector", "securityType",
               "securityType2",
               "securityDescription",
               "status_id", "name1", "exchange1", "name2", "market", "type", "currency",
               "country",
               "active",
               "exSymbol", "primaryExch"
            # ,"similar","tags"
               ]

        # col1 = ["similar","tags"]
        duplicates =  len(final_polygon) - len(final_polygon.drop_duplicates(inplace=False, subset='figi'))

        final_polygon = final_polygon[col]
        final_polygon.drop_duplicates(inplace=True, subset='figi')

        # array_df = final_polygon2[col1]

        #Pull symbols from database
        session=self.Session()
        symbols_db = session.query(Symbol).all()
        list_symbols_db = []
        for symbol in symbols_db:
            list_symbols_db.append(symbol.figi)

        exist_in_db = [x for x in final_polygon.index if (x in list_symbols_db)]
        not_in_db = [x for x in final_polygon.index if (x not in list_symbols_db)]

        final_polygon_exist = final_polygon.loc[exist_in_db]
        final_polygon_new = final_polygon.loc[not_in_db]


        try:
            session = self.Session()
            session.bulk_update_mappings(Symbol,final_polygon_exist.to_dict(orient='records'))
            print("Updated tickers",len(final_polygon_exist))

            session.bulk_insert_mappings(Symbol, final_polygon_new.to_dict(orient='records'))
            print("Inserted tickers", len(final_polygon_new))

            # session.bulk_update_mappings(Symbol, array_df.to_dict(orient='records'))


        except Exception as e:
            print(f"There was an Error inserting data. Error:{e}")
            session.rollback()
        finally:
            print("..")

            print("Ticker Detail",df)
            print("df1",df1)
            print("Total Tickers:", len(df))
            print("Tickers with details:", len(ticker_detail_df))
            print("Final Df:", len(final_df))
            print("final_df_w_figi:", len(final_df_w_figi))
            print("final_df_wo_figi:", len(final_df_wo_figi))
            print("Figi available for final_df_wo_figi:", len(df1))
            print("Outer Join:", len(Outer_join))
            print("final_polygon:", len(final_polygon))
            print("duplicates",duplicates)
            print("final_polygon_new:", len(final_polygon_new))
            print("final_polygon_exist:", len(final_polygon_exist))







        session.commit()







