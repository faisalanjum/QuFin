from typing import List, Optional
from pydantic import BaseModel
from datetime import date, datetime, time, timedelta

class UserBase(BaseModel):
    name : str
    email: str
    alpaca_secret: str
    alpaca_key: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

