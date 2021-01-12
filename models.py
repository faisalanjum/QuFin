from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date,DateTime
from sqlalchemy.sql import func


Base = declarative_base()

class User(Base):

    #tablename

    __tablename__="users"

    #columns
    id=Column("id",Integer,primary_key=True)

    name=Column("name",String,nullable=False)
    alpaca_secret=Column("alpaca_secret",String,nullable=False)
    alpaca_key=Column("alpaca_key",String,nullable=False)
    created_at=Column("created_at",DateTime(timezone=True),server_default=func.now())
    updated_at=Column("updated_at",DateTime(timezone=True),server_default=func.now())

    def __repr__(self):
        return "<User(name='{}', alpaca_secret='{}', alpaca_key={}, created_at={}, updated_at={})>" \
            .format(self.name, self.alpaca_secret, self.alpaca_key, self.created_at, self.updated_at)
