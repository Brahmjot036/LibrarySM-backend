Library Management System - Backend

📌 Overview

This is the backend for the Library Management System, built using FastAPI. It provides APIs for managing books, users, issuing and returning books, and membership subscriptions.

🚀 Features

User authentication (JWT-based)

Add, update, delete, and view books

Issue and return books

Membership management (add, extend, and track expiry)

Secure API with authentication & authorization

Fast and scalable with FastAPI

🛠️ Tech Stack

Backend: FastAPI (Python)

Database: PostgreSQL / SQLite (depending on environment)

Authentication: JWT (JSON Web Tokens)

Deployment: Docker, Uvicorn

Testing: Pytest



Clone the Repository

git clone https://github.com/your-username/library-management-backend.git
cd library-management-backend

3️⃣ Create a Virtual Environment & Install Dependencies

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

4️⃣ Set Up Environment Variables

Create a .env file in the root directory and add the following:

DATABASE_URL=postgresql://user:password@localhost/library_db
SECRET_KEY=your_jwt_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

5️⃣ Run Database Migrations

alembic upgrade head

6️⃣ Start the Server

uvicorn app.main:app --reload

7️⃣ API Documentation

Once the server is running, open your browser and go to:

Swagger UI: http://127.0.0.1:8000/docs

ReDoc: http://127.0.0.1:8000/redoc

🧪 Running Tests

pytest tests/

🐳 Running with Docker

docker build -t library-backend .
docker run -p 8000:8000 --env-file .env library-backend

📜 API Endpoints

🔑 Authentication

Method

Endpoint

Description

POST

/register

Register a user

POST

/login

Login & get token

📚 Books

Method

Endpoint

Description

GET

/books

Get all books

POST

/books

Add a new book

PUT

/books/{id}

Update a book

DELETE

/books/{id}

Delete a book

📖 Issue & Return Books

Method

Endpoint

Description

POST

/issue_book

Issue a book to a user

POST

/return_book

Return an issued book

🎫 Membership

Method

Endpoint

Description

POST

/add_membership

Add a membership

POST

/update_membership

Extend membership
