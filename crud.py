import config
from models import Base, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

engine = create_engine(config.DATABASE_URL)

# Base.metadata.drop_all(engine)
# Base.metadata.create_all(engine)

# def recreate_database():
#     Base.metadata.drop_all(engine)
#     Base.metadata.create_all(engine)

# recreate_database()

Session = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

user = User(
    name="Zidane",
    alpaca_secret="1",
    alpaca_key="786")

with session_scope() as s:
    s.add(user)
    print(s.query(User).all())





