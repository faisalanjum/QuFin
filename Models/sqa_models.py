from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date,DateTime, \
    UniqueConstraint, ForeignKey, Sequence, Text

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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


#Symbol Table
class Symbol(Base):
    __tablename__="symbol"
    __table_args__ = tuple([UniqueConstraint('figi')])

    id=Column("id",Integer,primary_key=True,autoincrement=True)
    ticker = Column("ticker", String)
    name =Column("name",String)
    figi = Column("figi", String)
    compositeFigi = Column("compositeFigi", String)
    exchCode = Column("exchCode", String)
    marketSector = Column("marketSector",String)
    securityType= Column("securityType",String)
    securityType2 = Column("securityType2",String)
    securityDescription = Column("securityDescription", String)
    shareClassFigi = Column("shareClassFigi",String)
    currency = Column("currency",String)

    created_at=Column("created_at",DateTime(timezone=True),server_default=func.now())
    updated_at=Column("updated_at",DateTime(timezone=True) , onupdate=func.now())

    def __repr__(self):
        return "<Symbol(ticker='{}', name='{}', figi='{}', compositefigi='{}', exchCode='{}', marketSector='{}', securityType='{}', " \
               "securityType2='{}', securityDescription='{}' ,shareClassFigi='{}', currency='{}', created_at={}, updated_at={})>" \
            .format(self.ticker, self.name, self.figi, self.compositeFigi, self.exchCode, self.marketSector, self.securityType,
                    self.securityType2,self.securityDescription, self.shareClassFigi, self.currency, self.created_at, self.updated_at)




