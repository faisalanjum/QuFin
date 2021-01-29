from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from Helper.helpers import remove_dupe_dicts, chunker
from Vendors.Alpaca import Alpaca
from Vendors.Polygon import Polygon
from Vendors.OpenFigi import OpenFigi
from Models.sqa_models import Symbol, VendorSymbol, Company, Forex, Indices, Crypto
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

        #Check if tickers are "Stocks" - May change some symbols later
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

        #Seperate out "STOCKS","INDICES","FX","CRYPTO"
        df_stocks =     df[df['market'] == 'STOCKS']
        df_indices =    df[df['market'] == 'INDICES']
        df_fx =         df[df['market'] == 'FX']
        df_crypto =     df[df['market'] == 'CRYPTO']

        fx_codes = ['currencyName', 'currency', 'baseName', 'base']
        for code in fx_codes:  #attrs will give error if you run testing line in get_tickers_threads as it requires all data to be populated first
            df_fx.loc[df_fx['attrs'].notnull(), code] = df_fx.loc[df_fx['attrs'].notnull(), 'attrs'].apply(lambda x: x.get(code))

        idx_codes = ['holiday', 'assettype', 'entitlement', 'disseminationfreq', 'dataset', 'schedule', 'brand',
                     'series']
        for code in idx_codes:
            df_indices.loc[df_indices['attrs'].notnull(), code] = df_indices.loc[df_indices['attrs'].notnull(), 'attrs'].apply(lambda x: x.get(code))

        crpt_codes = ['currencyName', 'currency', 'baseName', 'base']
        for code in crpt_codes:
            df_crypto.loc[df_crypto['attrs'].notnull(), code] = df_crypto.loc[df_crypto['attrs'].notnull(), 'attrs'].apply(lambda x: x.get(code))


        df_fx['ticker'] = df_fx.index
        df_fx['uniqueID'] = df_fx.index
        df_fx.index.name = 'uniqueID'
        df_fx.rename(columns={'locale': 'country'}, inplace=True)
        df_fx['vendor_id'] = 2
        df_fx['vendor_symbol'] = df_fx['ticker']

        df_indices['ticker'] = df_indices.index
        df_indices['uniqueID'] = df_indices.index
        df_indices.index.name = 'uniqueID'
        df_indices.rename(columns={'locale': 'country'}, inplace=True)
        df_indices['vendor_id'] = 2
        df_indices['vendor_symbol'] = df_indices['ticker']

        df_crypto['ticker'] = df_crypto.index
        df_crypto['uniqueID'] = df_crypto.index
        df_crypto.index.name = 'uniqueID'
        df_crypto.rename(columns={'locale': 'country'}, inplace=True)
        df_crypto['vendor_id'] = 2
        df_crypto['vendor_symbol'] = df_crypto['ticker']

        fx_cols1 = ['uniqueID', 'ticker', 'name', 'primaryExch', 'type', 'currency', 'market', 'country']
        fx_cols2 = ['ticker', 'name', 'currencyName', 'currency', 'baseName', 'base']  # make 'uniqueID' as index
        fx_cols3 = ['uniqueID','vendor_id']  # make 'uniqueID' as index
        df_fx_sym = df_fx[fx_cols1] # For Symbol Table
        df_fx_tbl = df_fx[fx_cols2] # For Forex Table
        df_fx_vs = df_fx[fx_cols3]  # For VendorSymbol Table

        idx_cols1 = ['uniqueID', 'ticker', 'name', 'primaryExch', 'type', 'currency', 'market', 'country']
        idx_cols2 = ['ticker', 'name', 'holiday','assettype','entitlement','disseminationfreq','dataset','schedule','brand','series']  # make 'uniqueID' as index
        idx_cols3 = ['uniqueID','vendor_id']  # make 'uniqueID' as index
        df_idx_sym = df_indices[idx_cols1] # For Symbol Table
        df_idx_tbl = df_indices[idx_cols2] # For Indices Table
        df_idx_vs = df_indices[idx_cols3]  # For VendorSymbol Table

        #crpto and FX have same columns
        df_cry_sym = df_crypto[fx_cols1] # For Symbol Table
        df_cry_tbl = df_crypto[fx_cols2] # For Forex Table
        df_cry_vs = df_crypto[fx_cols3]  # For VendorSymbol Table

            #Indices and Crypto to do similarly as Fx - remember "attr" dictionary is different for all
        # df_fx.set_index('ticker', inplace=True)

        stock_symbols = list(df_stocks.index.values)

        start_time = time.time()

        #Function to fetch Ticker Details from Polygon
        tickerdata = polygon.details(stock_symbols)

        # NEED TO CHECK IF ALL TICKERS ARE BEING LOADED - not done yet
        ticker_detail_df = pd.DataFrame.from_dict(tickerdata).set_index('symbol')
        print("---Ticker Details  %s Minutes ---" % ((time.time() - start_time) / 60))

        # Postfix "_d" to column names of "ticker_detail_df"
        new_column_names = [n + "_d" for n in list(ticker_detail_df.columns)]
        ticker_detail_df.columns = new_column_names

        # Combine both dfs - (1) Tickers(df) & (2) Ticker_Detail(ticker_detail_df)
        final_df_stock = pd.concat([df_stocks, ticker_detail_df], axis=1,join='outer',sort =False).rename_axis('ticker')

        # Seperate final_df into 2: One with Figi's and other without
        final_df_wo_figi = final_df_stock.copy()
        final_df_wo_figi = final_df_wo_figi[pd.isnull(final_df_wo_figi['figi'])]
        final_df_w_figi = final_df_stock[pd.notnull(final_df_stock['figi'])]
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

        final_polygon_stock = pd.concat([final_df_w_figi, Outer_join])

        # drop & rename columns
        final_polygon_stock['uniqueID'] = final_polygon_stock.index
        final_polygon_stock.rename(columns={'cfigi': 'compositeFigi'}, inplace=True)
        final_polygon_stock.rename(columns={'scfigi': 'shareClassFigi'}, inplace=True)

        #Compares Figi (which is uniqueID incase of Companies)  = CompFIGI
        # Issue is this will also overwrite with 1 after we've changed internal_code to say 2 when we create a new row for figi=compfigi
        final_polygon_stock['internal_code'] = [
            1 if (row['uniqueID'] == row['compositeFigi']) else 0 for index, row in
            final_polygon_stock.iterrows()]

        # fill these later using openfigi
        final_polygon_stock['securityType2'] = ''
        final_polygon_stock['securityDescription'] = None
        final_polygon_stock['exchCode'] = None

        # create new columns - similar & tags
        final_polygon_stock.rename(columns={'sector_d': 'marketSector'}, inplace=True)
        final_polygon_stock.rename(columns={'type_d': 'securityType'}, inplace=True)
        final_polygon_stock.rename(columns={'country_d': 'country'}, inplace=True)
        final_polygon_stock.rename(columns={'exchangeSymbol_d': 'exSymbol'}, inplace=True)
        final_polygon_stock.rename(columns={'similar_d': 'similar'}, inplace=True)
        final_polygon_stock.rename(columns={'tags_d': 'tags'}, inplace=True)

        final_polygon2 = final_polygon_stock.copy()

        col = ['uniqueID', 'ticker', "name", "compositeFigi", "shareClassFigi", "exchCode", "marketSector", "securityType",
               "securityType2",
               "securityDescription",
               "internal_code","market", "type", "currency",
               "country",
               "active",
               "exSymbol", "primaryExch"
            # ,"similar","tags"
               ]

        duplicates =  len(final_polygon_stock) - len(final_polygon_stock.drop_duplicates(inplace=False, subset='uniqueID'))
        final_polygon_stock = final_polygon_stock[col]
        final_polygon_stock.drop_duplicates(inplace=True, subset='uniqueID')

        #Simply removing where figi is available but compfigi is not - later try to fetch these as well
        not_present = ['', np.nan, None]
        print("final_polygon_stock before removing cfigi",len(final_polygon_stock))
        final_polygon_stock = final_polygon_stock.loc[~(final_polygon_stock['compositeFigi'].isin(not_present))]
        print("final_polygon_stock after removing cfigi", len(final_polygon_stock))

        #Add a new row with figi = compfigi where don't find compfigi = figi for all tickers
        extra_rows = final_polygon_stock.copy()
        extra_rows = extra_rows[extra_rows['internal_code'] == 0] #finds values where internal_code = 0
        extra_rows = extra_rows[extra_rows['active'] == True] # Pick only Active Tickers
        extra_rows = extra_rows.drop_duplicates(subset=['compositeFigi']) #remove duplicate values of cfigi

        #Remove those rows from extra_rows which have 'compositeFigi' equal to figi/uniqueID of final_polygon_stock
        extra_rows = extra_rows.loc[~extra_rows['compositeFigi'].isin(final_polygon_stock['uniqueID'].values)]

        dict_new_rows = [{
                'uniqueID': row['compositeFigi'],'ticker': row['ticker'],'name': row['name'],
                'compositeFigi': row['compositeFigi'],
                'shareClassFigi': row['shareClassFigi'],
                'exchCode': '','exSymbol': row['exSymbol'],'primaryExch': row['primaryExch'],
                'securityType': row['securityType'],'securityType2': row['securityType2'],
                'securityDescription': '',
                'market': row['market'],'type': row['type'],'marketSector': row['marketSector'],
                'currency': row['currency'],'country': row['country'],'active': row['active'],
                'internal_code': 2}for index, row in extra_rows.iterrows()]

        extra_rows_df = pd.DataFrame.from_dict(dict_new_rows)
        extra_index = []
        for i in range(len(dict_new_rows)):
            extra_index.append(dict_new_rows[i]['uniqueID'])
        extra_rows_df.index = extra_index

        # print("extra_rows_df - Before [col]", extra_rows_df)

        extra_rows_df = extra_rows_df[col]
        # print("extra_rows_df - After [col]", extra_rows_df)


        # print("final_polygon_stock", final_polygon_stock)
        # print("extra_rows_df.columns", extra_rows_df.columns)
        # print("final_polygon_stock.columns", final_polygon_stock.columns)

        # final_polygon_stock = pd.concat([final_polygon_stock, extra_rows_df ], axis=0)

        #Pull symbols from database
        session=self.Session()
        symbols_db = session.query(Symbol).all()
        list_symbols_db = []
        for symbol in symbols_db:
            list_symbols_db.append(symbol.uniqueID)

        extra_symbols = session.query(Symbol).filter_by(internal_code=2).all()
        list_extra_symbols_db = []
        for symbol in extra_symbols:
            list_extra_symbols_db.append(symbol.uniqueID)

        exist_in_db = [x for x in final_polygon_stock.index if (x in list_symbols_db)]
        not_in_db = [x for x in final_polygon_stock.index if (x not in list_symbols_db)]
        extra_to_be_inserted = [x for x in extra_rows_df.index if (x not in list_symbols_db)]
        extra_to_be_updated = list_extra_symbols_db

        #NEED TO UPDATE "extra_to_be_updated" in the database

        # print("final_polygon_stock.index",final_polygon_stock.index)
        # print("list_symbols_db",list_symbols_db)
        # print("extra_rows_df.index",extra_rows_df.index)

        final_polygon_exist = final_polygon_stock.loc[exist_in_db]
        final_polygon_new = final_polygon_stock.loc[not_in_db]
        extra_rows_df_new = extra_rows_df.loc[extra_to_be_inserted]

        #Pull data from VendorSymbol
        session=self.Session()
        vendorsymbol_db = session.query(VendorSymbol).filter((VendorSymbol.vendor_id == 2) | (VendorSymbol.vendor_id == 7 )).all()
        list_uniqueID = []
        for row in vendorsymbol_db:
                list_uniqueID.append(row.uniqueID)

        vendorsymbol_index = []

        #Check if a symbol has already been added in vendorsymbol for Polygon - Append a list with uniqueID if vendor_id = 2

        # For VendorSymbol Table
        dict_vendorsymbol_poly = [{"uniqueID": row['uniqueID'],"vendor_symbol": row['ticker'],"vendor_id": 2
                }for index, row in final_polygon_stock.iterrows()]
        df_vendorsymbol_poly = pd.DataFrame.from_dict(dict_vendorsymbol_poly)
        for i in range(len(dict_vendorsymbol_poly)):
            vendorsymbol_index.append(dict_vendorsymbol_poly[i]['uniqueID'])
        df_vendorsymbol_poly.index = vendorsymbol_index

        # print("df_vendorsymbol_poly -Before conditions", df_vendorsymbol_poly)
        vs_cond = [x for x in df_vendorsymbol_poly.index if (x not in list_uniqueID)]
        df_vendorsymbol_poly = df_vendorsymbol_poly.loc[vs_cond]

        # Need to write code to update vendorsymbol **IMPORTANT - TO CHECK IF extra_tickers(internal_code = 2 is being added to "vendorsymbol" table?

        # For Company Table - Polygon
        session = self.Session()
        company_db = session.query(Company).all()
        list_company = []
        for row in company_db:
                list_company.append(row.compositeFigi)

        print("list_company",list_company)

        final_polygon_stock = final_polygon_stock[extra_rows_df.columns.values]

        print("final_polygon_stock['internal_code']", final_polygon_stock['internal_code'])

        # **** IMPORTANT need to concatenate "final_polygon_stock" to extra_rows_df below in df_company_tbl -  not able to do
        # df_company_tbl = pd.concat([extra_rows_df] , axis=0)

        df_company_tbl = pd.concat([extra_rows_df,final_polygon_stock], axis=0)

        #to only pick tickers where ('internal_code'] == 1 i.e compFIGI = FIGI) or 'internal_code'] == 2 - where we created a new row with compfigi = figi)
        df_company_tbl = df_company_tbl.loc[((df_company_tbl['internal_code'] == 1) | (df_company_tbl['internal_code'] == 2))]

        print("final_polygon_stock['internal_code']",final_polygon_stock['internal_code'])
        print("df_company_tbl['internal_code']", df_company_tbl['internal_code'])
        print("extra_rows_df['internal_code']", extra_rows_df['internal_code'])
        print("extra_rows_df", extra_rows_df)
        print("df_company_tbl",df_company_tbl)

        # df_company_tbl['uniqueID'] = df_company_tbl.index
        df_dict_company_tbl = [{'uniqueID': row['uniqueID'],'name': row['name'],'ticker': row['ticker'],
                            'sector': row['marketSector'],
                            'description': row['securityDescription'],
                            'compositeFigi': row['compositeFigi']
                                }for index, row in df_company_tbl.iterrows()]

        df_company_tbl_ = pd.DataFrame.from_dict(df_dict_company_tbl)

        print("df_dict_company_tbl",df_dict_company_tbl)
        print("df_company_tbl_",df_company_tbl_)
        poly_company_index = []
        for i in range(len(df_dict_company_tbl)):
            poly_company_index.append(df_dict_company_tbl[i]['uniqueID'])
        df_company_tbl_.index = poly_company_index

        print("df_company_tbl_.index",df_company_tbl_.index)

        print("df_company_tbl_", df_company_tbl_)
        # df_company_tbl_.set_index('ticker', inplace = True)
        company_cond = [x for x in df_company_tbl_.index if (x not in list_company)]

        print("company_cond",company_cond)


        df_company_tbl_ = df_company_tbl_.loc[company_cond]

        try:
            session = self.Session()
            session.bulk_update_mappings(Symbol,final_polygon_exist.to_dict(orient='records'))
            print("Updated tickers",len(final_polygon_exist))

            session.bulk_insert_mappings(Symbol, final_polygon_new.to_dict(orient='records'))
            session.bulk_insert_mappings(Symbol, extra_rows_df_new.to_dict(orient='records'))
            session.bulk_insert_mappings(Symbol, df_fx_sym.to_dict(orient='records'))
            session.bulk_insert_mappings(Symbol, df_idx_sym.to_dict(orient='records'))
            session.bulk_insert_mappings(Symbol, df_cry_sym.to_dict(orient='records'))

            session.bulk_insert_mappings(Company, df_company_tbl_.to_dict(orient='records'))

            session.bulk_insert_mappings(Forex, df_fx_tbl.to_dict(orient='records'))
            session.bulk_insert_mappings(Indices, df_idx_tbl.to_dict(orient='records'))
            session.bulk_insert_mappings(Crypto, df_cry_tbl.to_dict(orient='records'))

            session.bulk_insert_mappings(VendorSymbol, df_vendorsymbol_poly.to_dict(orient='records'))

            session.bulk_insert_mappings(VendorSymbol, df_fx_vs.to_dict(orient='records'))
            session.bulk_insert_mappings(VendorSymbol, df_idx_vs.to_dict(orient='records'))
            session.bulk_insert_mappings(VendorSymbol, df_cry_vs.to_dict(orient='records'))

            print("Inserted tickers", len(final_polygon_new))
            print("Inserted Extra tickers", len(extra_rows_df_new))

        except Exception as e:
            print(f"There was an Error inserting data. Error:{e}")
            session.rollback()
        finally:
            print("Stocks df",df_stocks)
            print("df1",df1)
            print("Total Stocks:", len(df_stocks))
            print("Tickers with details:", len(ticker_detail_df))
            print("Final Df of Stocks:", len(final_df_stock))
            print("final_df_w_figi:", len(final_df_w_figi))
            print("final_df_wo_figi:", len(final_df_wo_figi))
            print("Figi available for final_df_wo_figi:", len(df1))
            print("Outer Join:", len(Outer_join))
            print("final_polygon:", len(final_polygon_stock))
            print("duplicates",duplicates)
            print("final_polygon_new:", len(final_polygon_new))
            print("final_polygon_exist:", len(final_polygon_exist))

            print("df_indices", df_indices)
            print("df_crypto", df_crypto)
            print("df_vendorsymbol_poly -After conditions", df_vendorsymbol_poly)
            print("df_company_tbl_", df_company_tbl_)

        session.commit()







