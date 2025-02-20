# schemas.py
from pydantic import BaseModel
from datetime import date

# User Schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: str
    password: str | None = None
    role: str | None = None
    action: str  # "new" or "update"

# Book Schemas
class BookCreate(BaseModel):
    title: str
    author: str

class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None

# Transaction Schemas
class IssueBook(BaseModel):
    user_id: int
    book_id: int

class ReturnBook(BaseModel):
    transaction_id: int

# Membership Schemas
class MembershipCreate(BaseModel):
    user_id: int
    duration: str | None = "6 months"

class MembershipUpdate(BaseModel):
    membership_id: int
    action: str  # "extend" or "cancel"
    duration: str | None = "6 months"
