# FastAPI Folder Structure

## Description
This is a FastAPI-powered REST API for authentication and data management. The service uses SQLAlchemy with PostgreSQL for persistence, Alembic for schema migrations, and Pydantic for robust configuration and validation. It supports JWT-based auth, efficient querying with pagination/filtering/sorting.

## 🚀 Features
- Fast, typed REST API built with FastAPI and Pydantic models
- Authentication and authorization:
  - OAuth2/JWT-based authentication
- Database layer:
  - SQLAlchemy ORM with PostgreSQL
  - Alembic migrations for versioned schemas
- Query capabilities:
  - Standard CRUD patterns
  - Pagination, filtering, and sorting best practices
- Blog System:
  - Complete Blog CRUD
  - Like/Unlike functionality
  - Comment system with single-level replies
- Configuration and environments:
  - .env-driven settings with Pydantic
- Testing:
  - Pytest test suite scaffolding
- Developer experience:
  - Automatic interactive API docs (Swagger UI and ReDoc) via FastAPI
  - Clear project structure suitable for growth and modularization


## 🛠️ Tech Stack

- **Back-end Framework**: FastAPI

- **Database**: SQL Alchemy ORM with PostgreSQL.

- **Authentication**: OAuth2/JWT.

- **Environment Management**: Pydantic & dotenv

- **Testing**: Pytest


## 🔧  Environment Setup

To run this project locally, you need to create and activate a Python virtual environment and install the required dependencies. Below are setup instructions for **Linux**, **Windows**, and **mac OS** systems.

1. **Clone the repository.**

2. **Create and Activate Virtual Environment.**

   #####  Linux / mac OS

   ```
   # Create a virtual environment named "venv"
   python3 -m venv venv
   
   # Activate the virtual environment
   source venv/bin/activate
   ```

   #####  Windows (CMD)

   ```
   :: Create virtual environment
   python -m venv venv
   
   :: Activate virtual environment
   venv\Scripts\activate
   ```

   

3. **Install Dependencies**

   Once the environment is activated:

   ```
   pip install -r requirements.txt
   ```

   

4. ##### Set Up Environment Variables

   Create a `.env` file in the project root directory as instructed in `.sample-env` file in this repository. 

   Example:

   ```
   # Database Configuration
   DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
   
   # JWT Configuration
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

   

## **🛠️ Alembic Configuration**

   To handle database schema migrations, this project uses **Alembic** with async SQLAlchemy support.

   #### 🔄 Running Alembic Migrations

   1. **Initialize Alembic (first time only):**

   ```
   alembic init alembic
   ```

   1. **Edit `alembic.ini` and `env.py` to use your database URL and async engine**.
       For detailed instructions and examples, follow this excellent guide:
       🔗 [Setup FastAPI project with async SQLAlchemy, Alembic, PostgreSQL and Docker](https://berkkaraal.com/blog/2024/09/19/setup-fastapi-project-with-async-sqlalchemy-2-alembic-postgresql-and-docker/#setup-database-migrations-with-alembic)
   2. **Create a migration revision:**

   ```
   alembic revision --autogenerate -m "Initial migration"
   ```

3. **Apply migrations:**

   ```
   alembic upgrade head
   ```

   > ✅ Use Alembic only when your virtual environment is activated and your database is running.



### ▶️ Run the Project

After setting up your environment and installing dependencies, follow these steps to start the FastAPI server:

#### 🔹 Start the Application

```
uvicorn main:socket_app --reload
```






