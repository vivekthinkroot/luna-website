
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    gender: GenderEnum = Field(...)
    birth_datetime: datetime = Field(...)
    birth_place: str = Field(..., min_length=1, max_length=100)
    birth_location_id: Optional[int] = None
    mobile_no: str = Field(..., min_length=10, max_length=15)
    email: EmailStr

class ProfileResponse(BaseModel):
    profile_id: UUID
    name: str
    gender: GenderEnum
    birth_datetime: datetime
    birth_place: str
    birth_location_id: Optional[int] = None
    mobile_no: str
    email: EmailStr
    sun_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
