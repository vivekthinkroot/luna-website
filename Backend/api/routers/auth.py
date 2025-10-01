from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import hashlib

from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from config.settings import get_settings

router = APIRouter(prefix="/authentication", tags=["Authentication"])

# Use DATABASE_URL from settings
settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.database.url
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

import uuid

class UserDB(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    mobile_no = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

from enum import Enum
from typing import Optional
from datetime import datetime as dt
from pydantic import Field

class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class UserSignup(BaseModel):
    email: EmailStr
    mobile_no: str = Field(..., min_length=10, max_length=15)
    password: str

class User(BaseModel):
    id: str
    email: str
    mobile_no: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


def create_user_id() -> str:
    return str(uuid.uuid4())

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/authentication/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(user: UserSignup, db: Session = Depends(get_db)):
    user_id = create_user_id()
    # Check if user exists by email or mobile_no
    existing = db.query(UserDB).filter((UserDB.email == user.email) | (UserDB.mobile_no == user.mobile_no)).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    db_user = UserDB(
        id=user_id,
        email=user.email,
        mobile_no=user.mobile_no,
        password_hash=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"success": True, "user": {
        "id": db_user.id,
        "email": db_user.email,
        "mobile_no": db_user.mobile_no
    }, "message": "User created successfully"}

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter((UserDB.email == form_data.username) | (UserDB.mobile_no == form_data.username)).first()
    if user and verify_password(form_data.password, user.password_hash):
        return {"access_token": user.id, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Incorrect username or password")

@router.get("/me")
def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = db.query(UserDB).filter(UserDB.id == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "id": user.id,
        "email": user.email,
        "mobile_no": user.mobile_no
    }
