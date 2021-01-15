from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from Models import db_util
from Schemas import pyd_schemas
from Models.db_util import SessionLocal

app = FastAPI()

# Get Names of Users
@app.get("/users/{user_id}", response_model=pyd_schemas.User)
def read_user(user_id: int, db: Session = Depends(db_util.get_db)):
    db_user = db_util.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Create Users
@app.post("/users/", response_model=pyd_schemas.User)
def create_user(user: pyd_schemas.UserCreate, db: Session = Depends(db_util.get_db)):
    db_user = db_util.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return db_util.create_user(db=db, user=user)

# Create Symbols
@app.post("/symbol/", response_model=pyd_schemas.Symbol)
def create_symbol(symbol: pyd_schemas.SymbolBase, db: Session = Depends(db_util.get_db)):
    db_symbol = db_util.get_symbol_by_uniqueID(db, uniqueID=symbol.uniqueID)
    if db_symbol:
        raise HTTPException(status_code=400, detail="Symbol already exists")
    return db_util.create_symbol(db=db, symbol=symbol)
