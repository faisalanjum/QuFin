
import config
from Models import sqa_models
from Schemas import pyd_schemas
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

engine = create_engine(config.DATABASE_URL)
# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#trial user - can delete later
user = sqa_models.User(
    name="newname",
    email = "nanu@gmail.com",
    alpaca_secret="787",
    alpaca_key="98712")

# utility functions to retrieve data
def get_user(db: Session, user_id: int):
    return db.query(sqa_models.User).filter(sqa_models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(sqa_models.User).offset(skip).limit(limit).all()

def get_user_by_email(db: Session, email: str):
    return db.query(sqa_models.User).filter(sqa_models.User.email == email).first()

def get_symbol_by_uniqueID(db: Session, uniqueID: str):
    return db.query(sqa_models.Symbol).filter(sqa_models.Symbol.uniqueID == uniqueID).first()

# utility functions to create data
def create_user(db: Session, user: pyd_schemas.UserCreate):
    db_user = sqa_models.User(email=user.email, password=user.password,
                              name = user.name, alpaca_secret = user.alpaca_secret,
                              alpaca_key = user.alpaca_key)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_symbol(db: Session, symbol: pyd_schemas.SymbolBase):
    db_symbol = sqa_models.Symbol(name=symbol.name, ticker=symbol.ticker, exchCode = symbol.exchCode,
                                  marketSector = symbol.marketSector, securityType = symbol.securityType,
                                  securityType2 = symbol.securityType2, shareClassFigi=symbol.shareClassFigi,
                                  currency=symbol.currency, uniqueID=symbol.uniqueID, status_ID =symbol.status_ID)
    db.add(db_symbol)
    db.commit()
    db.refresh(db_symbol)
    return db_symbol




