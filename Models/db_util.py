
import config
from Models import sqa_models
from Schemas import pyd_schemas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from Models.sqa_models import Symbol, User, Company, Forex, StockPriceDaily, StockAdjustment, VendorSymbol, Vendor

engine = create_engine(config.DATABASE_URL)

# Vendor.__table__.drop(engine)
# StockAdjustment.__table__.create(engine)

# sqa_models.Base.metadata.drop_all(engine)
sqa_models.Base.metadata.create_all(engine)


SessionLocal = sessionmaker(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# user - can delete later
# user = sqa_models.User(
#     name="newname",
#     email = "nanu@gmail.com",
#     alpaca_secret="787",
#     alpaca_key="98712")
#
# # utility functions to retrieve data
# def get_user(db: Session, user_id: int):
#     return db.query(sqa_models.User).filter(sqa_models.User.id == user_id).first()
#
# def get_users(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(sqa_models.User).offset(skip).limit(limit).all()
#
# def get_user_by_email(db: Session, email: str):
#     return db.query(sqa_models.User).filter(sqa_models.User.email == email).first()
#
# def get_symbol_by_figi(db: Session, figi: str):
#     return db.query(sqa_models.Symbol).filter(sqa_models.Symbol.figi == figi).first()




#delete this
def get_symbol_by_figi(db: Session, figi: str):
    return db.query(sqa_models.Symbol).filter(sqa_models.Symbol.figi == figi).first()


#delete this
def get_company_by_figi(db: Session, compositeFigi: str):
    return db.query(sqa_models.Company).filter(sqa_models.Company.compositeFigi == compositeFigi).first()

#delete this
def get_forex_by_figi(db: Session, compositeFigi: str):
    return db.query(sqa_models.Forex).filter(sqa_models.Forex.compositeFigi == compositeFigi).first()


# utility functions to create data
# def create_user(db: Session, user: pyd_schemas.UserCreate):
#     db_user = sqa_models.User(email=user.email, password=user.password,
#                               name = user.name, alpaca_secret = user.alpaca_secret,
#                               alpaca_key = user.alpaca_key)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user

# def create_symbol(db: Session, symbol: pyd_schemas.SymbolBase):
#     db_symbol = sqa_models.Symbol(ticker=symbol.ticker, name=symbol.name,
#               figi=symbol.figi,compositeFigi=symbol.compositeFigi,
#               exchCode = symbol.exchCode,marketSector = symbol.marketSector, securityType = symbol.securityType,
#               securityType2 = symbol.securityType2, securityDescription = symbol.securityDescription,
#               shareClassFigi=symbol.shareClassFigi,currency=symbol.currency)
#
#     db.add(db_symbol)
#     db.commit()
#     db.refresh(db_symbol)
#     return db_symbol

#delete this
def create_symbol(db: Session, symbol: pyd_schemas.SymbolBase):
    db_symbol = sqa_models.Symbol(ticker=symbol.ticker, name=symbol.name,
    figi=symbol.figi,compositeFigi=symbol.compositeFigi, numbers=symbol.numbers, status_id =symbol.status_id)

    db.add(db_symbol)
    db.commit()
    db.refresh(db_symbol)
    return db_symbol


#delete this
def create_company(db: Session, symbol: pyd_schemas.CompanyBase):
    db_company = sqa_models.Company(ticker=symbol.ticker, name=symbol.name
        ,compositeFigi=symbol.compositeFigi)

    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

#delete this
def create_forex(db: Session, symbol: pyd_schemas.ForexBase):
    db_forex = sqa_models.Forex(ticker=symbol.ticker, name=symbol.name
        ,compositeFigi=symbol.compositeFigi)

    db.add(db_forex)
    db.commit()
    db.refresh(db_forex)
    return db_forex

