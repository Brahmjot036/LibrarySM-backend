# seed.py
import asyncio
from database import engine, async_session
from models import Base, User, Book
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        # Create sample users
        admin = User(username="admin", password=pwd_context.hash("admin123"), role="Admin")
        user1 = User(username="user1", password=pwd_context.hash("user123"), role="User")
        session.add_all([admin, user1])
        await session.commit()
        # Create sample books (for demonstration, 10 books)
        books = []
        for i in range(1, 11):
            book = Book(title=f"Sample Book Title {i}", author=f"Author {i}", available=True)
            books.append(book)
        session.add_all(books)
        await session.commit()
        print("Database seeded with sample users and books!")

if __name__ == "__main__":
    asyncio.run(seed())
