from typing import List
from fastapi import Depends, FastAPI, HTTPException

from sqlalchemy.orm import Session
from contextlib import contextmanager

import config, schemas, models, crud
from models import Base
from crud import SessionLocal, engine, session_scope


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
# with session_scope not working in api calls since included exception in it but get_dbworks.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)
