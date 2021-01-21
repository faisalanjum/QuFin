from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime, time, timedelta

# class UserBase(BaseModel):
#     name : str
#     email: str
#     alpaca_secret: str
#     alpaca_key: str
#
# class UserCreate(UserBase):
#     password: str
#
# class User(UserBase):
#     id: int
#
#     created_at: datetime
#     updated_at: datetime
#
#     class Config:
#         orm_mode = True
#
# class SymbolBase(BaseModel):
#
#     ticker: str
#     name: str
#     figi: str
#     compositeFigi: str
#     exchCode: str
#     marketSector: str
#     securityType: str
#     securityType2: str
#     securityDescription: str
#     shareClassFigi: str
#     currency: str
#
# class Symbol(SymbolBase):
#     id: int
#     created_at: datetime
#     updated_at: Optional[datetime]
#
#     class Config:
#         orm_mode = True


#DELETE THIS
class SymbolBase(BaseModel):

    ticker: str
    name: str
    figi: str
    numbers: List[int]
    compositeFigi: str
    status_id: bool

class Symbol(SymbolBase):
    id: int

    class Config:
        orm_mode = True

class CompanyBase(BaseModel):
    ticker: str
    name: str
    compositeFigi: str

class Company(CompanyBase):
    id: int

    class Config:
        orm_mode = True


class ForexBase(BaseModel):
    ticker: str
    name: str
    compositeFigi: str

class Forex(ForexBase):
    id: int

    class Config:
        orm_mode = True

