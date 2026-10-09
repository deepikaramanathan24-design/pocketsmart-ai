from pydantic import BaseModel, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str

class HomeRequest(BaseModel):
    user_id: int
    budget: float
    room: str
    style: str

class PartyRequest(BaseModel):
    user_id: int
    budget: float
    event_type: str
    guests: int
    theme: str

class JewelryRequest(BaseModel):
    user_id: int
    budget: float
    jewelry_type: str
    occasion: str
    style: str
