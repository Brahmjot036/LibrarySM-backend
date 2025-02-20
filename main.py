# main.py
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, date
from passlib.context import CryptContext
import jwt
from dotenv import load_dotenv

from database import async_session, engine
from models import Base, User, Book, Membership, Transaction
from schemas import UserCreate, UserLogin, BookCreate, BookUpdate, IssueBook, ReturnBook, MembershipCreate, MembershipUpdate

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="Library Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency for database session
async def get_db():
    async with async_session() as session:
        yield session

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt

# ---------------- User Auth ----------------
@app.post("/signup")
async def signup(user: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == user.username)
    result = await db.execute(stmt)
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = get_password_hash(user.password)
    new_user = User(username=user.username, password=hashed_pw, role=user.role)
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Error creating user")
    return {"message": "User signed up successfully"}

@app.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == user.username)
    result = await db.execute(stmt)
    db_user = result.scalars().first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"token": access_token, "role": db_user.role}

# ---------------- Book CRUD ----------------
@app.get("/books")
async def get_books(db: AsyncSession = Depends(get_db)):
    stmt = select(Book)
    result = await db.execute(stmt)
    books = result.scalars().all()
    return [{"id": b.id, "title": b.title, "author": b.author, "available": b.available} for b in books]

@app.post("/books")
async def add_book(book: BookCreate, db: AsyncSession = Depends(get_db)):
    new_book = Book(title=book.title, author=book.author, available=True)
    db.add(new_book)
    await db.commit()
    await db.refresh(new_book)
    return {"message": "Book added", "book": {"id": new_book.id, "title": new_book.title}}

@app.put("/books/{book_id}")
async def update_book(book_id: int, book_data: BookUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Book).where(Book.id == book_id)
    result = await db.execute(stmt)
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book_data.title:
        book.title = book_data.title
    if book_data.author:
        book.author = book_data.author
    await db.commit()
    return {"message": "Book updated"}

@app.delete("/books/{book_id}")
async def delete_book(book_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Book).where(Book.id == book_id)
    result = await db.execute(stmt)
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    await db.delete(book)
    await db.commit()
    return {"message": "Book deleted"}

# ---------------- Issue / Return ----------------
@app.post("/issue_book")
async def issue_book(issue: IssueBook, db: AsyncSession = Depends(get_db)):
    stmt = select(Book).where(Book.id == issue.book_id)
    result = await db.execute(stmt)
    book = result.scalars().first()
    if not book or not book.available:
        raise HTTPException(status_code=400, detail="Book not available")
    issue_date = date.today()
    return_date = issue_date + timedelta(days=15)
    transaction = Transaction(user_id=issue.user_id, book_id=issue.book_id, issue_date=issue_date, return_date=return_date)
    book.available = False
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return {"message": "Book issued", "transaction_id": transaction.id}

@app.post("/return_book")
async def return_book(ret: ReturnBook, db: AsyncSession = Depends(get_db)):
    stmt = select(Transaction).where(Transaction.id == ret.transaction_id)
    result = await db.execute(stmt)
    transaction = result.scalars().first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    stmt = select(Book).where(Book.id == transaction.book_id)
    result = await db.execute(stmt)
    book = result.scalars().first()
    if book:
        book.available = True
    await db.commit()
    return {"message": "Book returned"}

# ---------------- Membership Management ----------------
@app.post("/add_membership")
async def add_membership(membership: MembershipCreate, db: AsyncSession = Depends(get_db)):
    if membership.duration == "6 months":
        expiry = date.today() + timedelta(days=180)
    elif membership.duration == "1 year":
        expiry = date.today() + timedelta(days=365)
    elif membership.duration == "2 years":
        expiry = date.today() + timedelta(days=730)
    else:
        raise HTTPException(status_code=400, detail="Invalid membership duration")
    new_membership = Membership(user_id=membership.user_id, expiry_date=expiry)
    db.add(new_membership)
    await db.commit()
    await db.refresh(new_membership)
    return {"message": "Membership added", "expiry_date": new_membership.expiry_date.isoformat()}

@app.post("/update_membership")
async def update_membership(update: MembershipUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Membership).where(Membership.id == update.membership_id)
    result = await db.execute(stmt)
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    if update.action.lower() == "extend":
        if update.duration == "6 months":
            extension = timedelta(days=180)
        elif update.duration == "1 year":
            extension = timedelta(days=365)
        elif update.duration == "2 years":
            extension = timedelta(days=730)
        else:
            raise HTTPException(status_code=400, detail="Invalid duration")
        membership.expiry_date += extension
        await db.commit()
        return {"message": "Membership extended", "new_expiry_date": membership.expiry_date.isoformat()}
    elif update.action.lower() == "cancel":
        await db.delete(membership)
        await db.commit()
        return {"message": "Membership canceled"}
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

# ---------------- Create Tables on Startup ----------------
@app.on_event("startup")
async def startup():
    from models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
# Add this endpoint at the end of main.py (after other endpoints)
@app.get("/dashboard_data")
async def dashboard_data(db: AsyncSession = Depends(get_db)):
    # Total books
    stmt_total = select(Book)
    result_total = await db.execute(stmt_total)
    books = result_total.scalars().all()
    total_books = len(books)
    
    # Issued books (books that are not available)
    issued_books = len([b for b in books if not b.available])
    
    # You can also add additional information as needed.
    return {"issued_books": issued_books, "total_books": total_books}
@app.get("/memberships")
async def get_memberships(db: AsyncSession = Depends(get_db)):
    stmt = select(Membership)
    result = await db.execute(stmt)
    memberships = result.scalars().all()
    # Return membership data as a list of dicts
    return [{"id": m.id, "user_id": m.user_id, "expiry_date": m.expiry_date.isoformat()} for m in memberships]
