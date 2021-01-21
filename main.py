from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from Models import db_util
from Schemas import pyd_schemas
from Models.db_util import SessionLocal
from Views import SymbolController

# app = FastAPI()

# Get Names of Users
# @app.get("/users/{user_id}", response_model=pyd_schemas.User)
# def read_user(user_id: int, db: Session = Depends(db_util.get_db)):
#     db_user = db_util.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user

# Create Users
# @app.post("/users/", response_model=pyd_schemas.User)
# def create_user(user: pyd_schemas.UserCreate, db: Session = Depends(db_util.get_db)):
#     db_user = db_util.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return db_util.create_user(db=db, user=user)
#
# # Create Symbols
# @app.post("/symbol/", response_model=pyd_schemas.Symbol)
# def create_symbol(symbol: pyd_schemas.SymbolBase, db: Session = Depends(db_util.get_db)):
#     db_symbol = db_util.get_symbol_by_figi(db, figi=symbol.figi)
#     if db_symbol:
#         raise HTTPException(status_code=400, detail="Figi already exists")
#     return db_util.create_symbol(db=db, symbol=symbol)


# def populate_symbols():
#     sym_obj=SymbolController.SymbolController()
#     dict = sym_obj.bulkInsertFromProviders("Alpaca")
#     print("dict",dict)
#     ticker_list, exchange_list, name_list = sym_obj.get_lists(dict)
#     print("ticker_list",ticker_list)
#     sym_obj.create_dictionary(ticker_list, name_list)
# populate_symbols()


#delete
# # Create Symbol
# @app.post("/symbol/", response_model=pyd_schemas.Symbol)
# def create_symbol(symbol: pyd_schemas.SymbolBase, db: Session = Depends(db_util.get_db)):
#     db_symbol = db_util.get_symbol_by_figi(db, figi=symbol.figi)
#     if db_symbol:
#         raise HTTPException(status_code=400, detail="Figi already exists")
#     return db_util.create_symbol(db=db, symbol=symbol)

# #delete
# # Create Company
# @app.post("/company/", response_model=pyd_schemas.Company)
# def create_company(company: pyd_schemas.CompanyBase, db: Session = Depends(db_util.get_db)):
#     db_symbol = db_util.get_company_by_figi(db, compositeFigi=company.compositeFigi)
#     if db_symbol:
#         raise HTTPException(status_code=400, detail="CompFigi already exists")
#     return db_util.create_company(db=db, symbol=company)


def populate_symbol():

    sym_obj=SymbolController.SymbolController()
    dict = sym_obj.bulkInsertFromProviders("Alpaca")

    # print("dict",dict)

    ticker_list, exchange_list, name_list = sym_obj.get_lists(dict)

    # print("ticker_list",ticker_list)
    sym_obj.create_dictionary(ticker_list, name_list)

populate_symbol()

from Models.sqa_models import Company, Symbol, Forex


# new_company = Company(
#     ticker = 'PACK1',
#     name = 'new',
#     compositeFigi = 'BBG000BDHB87')

# new_forex = Forex(
#     ticker = 'PACK2',
#     name = 'new1',
#     compositeFigi = 'BBG000PTSB12')

# new_symbol = Symbol(
#     ticker = 'UFS',
#     name = 'DOMTAR CORPORATION (New)',
#     figi = 'BBG000BHFHP8',
#     compositeFigi = 'BBG000BHFHP8',
#     status_id = True
# )

# session = SessionLocal()
# # session.add(new_company)
# session.add(new_forex)
# session.commit()
# session.close()


session = SessionLocal()
one = session.query(Symbol).filter(Symbol.status_id == 'True').all()
for on in one:

    som = session.query(Forex).filter(Forex.compositeFigi == on.figi).first()

    if(som):
        pass
    else:

        new_forex = Forex(
            ticker = on.ticker,
            name = on.name,
            compositeFigi = on.figi)

        try:
            print(on.figi)
            session.add(new_forex)
            session.commit()

        except:
            pass

session.close()