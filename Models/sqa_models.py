from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date,DateTime, \
    UniqueConstraint, ForeignKey, Sequence, Text, Boolean, Float, Enum, BigInteger

from sqlalchemy.dialects import postgresql

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.event import listens_for
import enum

import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# from Models.db_util import SessionLocal

Base = declarative_base()

class User(Base):
    __tablename__="users"

    id=Column("id",Integer,primary_key=True,index=True)

    name=Column("name",String,nullable=False,index=True)
    email = Column("email", String,index=True)
    password = Column("password",String,index=True)
    alpaca_secret=Column("alpaca_secret",String,nullable=False)
    alpaca_key=Column("alpaca_key",String,nullable=False)
    created_at=Column("created_at",DateTime(timezone=True),server_default=func.now())
    updated_at=Column("updated_at",DateTime(timezone=True),server_default=func.now())

    def __repr__(self):
        return "<User(name='{}',email='{}', password='{}', alpaca_secret='{}', alpaca_key='{}', created_at={}, updated_at={})>" \
            .format(self.name,self.email,self.password, self.alpaca_secret, self.alpaca_key, self.created_at, self.updated_at)



    # id=Column("id",Integer,primary_key=True,autoincrement=True)

class Symbol(Base):
    __tablename__="symbol"
    # __table_args__ = tuple([UniqueConstraint('figi')])

    figi = Column("figi", String, primary_key=True)

    ticker = Column("ticker", String)
    name =Column("name",String)


    compositeFigi = Column("compositeFigi",String)
    shareClassFigi = Column("shareClassFigi", String)
    exchCode = Column("exchCode", String)

    marketSector = Column("marketSector", String)
    securityType= Column("securityType",String)
    securityType2 = Column("securityType2",String)
    securityDescription = Column("securityDescription", String)
    uniqueIDFutOpt = Column(String)

    status_id = Column("status_id", Boolean)

    #from Alpaca
    name1 = Column("name1", String)
    exchange1 = Column("exchange1", String)

    #from Polygon
    name2 = Column("name2", String)
    market = Column("market", String)
    type = Column("type", String)
    currency = Column("currency", String)
    country = Column("country", String)
    active = Column("active", String)
    exSymbol = Column("exSymbol", String)
    primaryExch = Column("primaryExch", String)

    created_at=Column("created_at",DateTime(timezone=True),server_default=func.now())
    updated_at=Column("updated_at",DateTime(timezone=True) , onupdate=func.now())

#     def __repr__(self):
#         return "<Symbol(ticker='{}', name='{}', figi='{}', compositefigi='{}', exchCode='{}', marketSector='{}', securityType='{}', " \
#                "securityType2='{}', securityDescription='{}' ,shareClassFigi='{}', currency='{}', created_at={}, updated_at={})>" \
#             .format(self.ticker, self.name, self.figi, self.compositeFigi, self.exchCode, self.marketSector, self.securityType,
#                     self.securityType2,self.securityDescription, self.shareClassFigi, self.currency, self.created_at, self.updated_at)


class Company(Base):
    __tablename__="company"
    # __table_args__ = tuple([UniqueConstraint('compositeFigi')])
    # id = Column("id", Integer, primary_key=True, autoincrement=True)

    name = Column("name", String)
    ticker = Column("ticker", String)
    cik = Column("cik", String)
    sic = Column("sic", String)  #for Industry classification
    industry = Column("industry", String)
    sector = Column("sector", String)
    url = Column("url", String)
    description = Column("description", String)

    tags = Column("tags",postgresql.ARRAY(String))
    similar = Column("similar",postgresql.ARRAY(String))

    compositeFigi = Column(String, ForeignKey('symbol.figi',
                                              onupdate='CASCADE',
                                              ondelete='CASCADE'), primary_key=True)
    symbol = relationship("Symbol", backref=backref("company", uselist=False))

    created_at=Column("created_at",DateTime(timezone=True),server_default=func.now())
    updated_at=Column("updated_at",DateTime(timezone=True) , onupdate=func.now())


# To do - other asset classes like (1) Forex, (2) Futures, (3) Options, (4) Bonds, (5) Macro, (6) Crypto
class Forex(Base):
    __tablename__="forex"

    # __table_args__ = tuple([UniqueConstraint('compositeFigi')])
    # id=Column("id",Integer,primary_key=True,autoincrement=True)

    ticker = Column("ticker", String)
    name =Column("name",String)
    compositeFigi = Column(String, ForeignKey('symbol.figi',
                                              onupdate='CASCADE',
                                              ondelete='CASCADE'), primary_key=True)
    # compositeFigi = Column("compositeFigi",String)
    symbol = relationship("Symbol", backref=backref("forex", uselist=False))


class VendorNames(enum.Enum):
    Alpaca = 'Alpaca'
    Polygon = 'Polygon'
    InteractiveBrokers = 'Interactive Brokers'
    SimFin = 'Sim Fin'
    AlphaVantage = 'Alpha Vantage'
    Quandl = 'Quandl'

class Vendor(Base):
    __tablename__="vendor"
    __table_args__ = tuple([UniqueConstraint('id')])

    id=Column("id",Integer,primary_key=True,autoincrement=True)
    name =Column("name", Enum(VendorNames),nullable=False)

    created_at=Column("created_at",DateTime(timezone=True),server_default=func.now())
    updated_at=Column("updated_at",DateTime(timezone=True) , onupdate=func.now())

# To do (1) Daily - already done (2) Intraday - 1m (S&P500 only) (3) Realtime (how to?)
class StockPriceDaily(Base):
    __tablename__="stockpricedaily"
    id=Column(Integer,primary_key=True,autoincrement=True)

    __table_args__ = tuple([UniqueConstraint('vendor_id', 'figi', "datetime")])

    figi = Column(String, ForeignKey('symbol.figi'))
    vendor_id = Column(Integer, ForeignKey('vendor.id'))
    company_id = Column(String, ForeignKey('company.compositeFigi'))

    datetime = Column(DateTime, nullable=False)

    open=Column(Float,nullable=False)
    high=Column(Float,nullable=False)
    low=Column(Float,nullable=False)
    close=Column(Float,nullable=False)
    volume=Column(BigInteger,nullable=False)

    adj_open=Column(Float,nullable=True)
    adj_high=Column(Float,nullable=True)
    adj_low=Column(Float,nullable=True)
    adj_close=Column(Float,nullable=True)
    adj_volume=Column(Float,nullable=True)

    symbol = relationship("Symbol", backref="stockpricedaily")
    company = relationship("Company", backref="stockpricedaily")
    vendor = relationship("Vendor", backref="stockpricedaily")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class StockAdjustment(Base):
    __tablename__="stockadjustment"
    __table_args__ = tuple([UniqueConstraint('vendor_id', 'company_id', "datetime")])

    id=Column("id",Integer,primary_key=True,autoincrement=True)

    vendor_id = Column(Integer, ForeignKey('vendor.id'))
    company_id = Column(String, ForeignKey('company.compositeFigi'))

    datetime = Column(DateTime,nullable=False)
    divident_amount = Column(Float, nullable=False)
    split_coef = Column(Float,nullable=False)
    shares_outstanding = Column(BigInteger,nullable=False)

    company = relationship("Company", backref="stockadjustment")
    vendor = relationship("Vendor", backref="stockadjustment")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class VendorSymbol(Base):
    __tablename__="vendorsymbol"
    __table_args__ = tuple([UniqueConstraint('vendor_id', 'figi')])

    id=Column("id",Integer,primary_key=True,autoincrement=True)
    vendor_symbol = Column("vendor_symbol", String)

    figi = Column(String, ForeignKey('symbol.figi'))
    vendor_id = Column(Integer, ForeignKey('vendor.id'))

    symbol = relationship("Symbol", backref="vendorsymbol")
    vendor = relationship("Vendor", backref="vendorsymbol")

    created_at=Column("created_at",DateTime(timezone=True),server_default=func.now())
    updated_at=Column("updated_at",DateTime(timezone=True) , onupdate=func.now())


Alpaca = Vendor(name='Alpaca')
Polygon = Vendor(name='Polygon')
InteractiveBrokers = Vendor(name='InteractiveBrokers')
SimFin = Vendor(name='SimFin')
AlphaVantage = Vendor(name='AlphaVantage')
Quandl = Vendor(name='Quandl')

@listens_for(Vendor.__table__, 'after_create')
def insert_initial_values(self,*args, **kwargs):

    self.url =config.DB_URL
    self.Session =sessionmaker()
    engine =create_engine(self.url)
    self.Session.configure(bind=engine)
    session =self.Session()

    session.add(Alpaca)
    session.add(Polygon)
    session.add(InteractiveBrokers)
    session.add(SimFin)
    session.add(AlphaVantage)
    session.add(Quandl)
    session.commit()

