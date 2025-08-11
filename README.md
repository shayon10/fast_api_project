A production-style **FastAPI** project with **JWT authentication**, **user management**, and **CRUD Todo** functionality.  
Perfect for showcasing backend development skills in your resume and GitHub portfolio.

---

## 📌 Features
- **JWT Authentication** (Sign Up & Login)
- **User Management** (Get current user profile)
- **Todo CRUD** (Create, List, Get, Update, Delete)
- **Search & Pagination**
- **SQLite Database** (Easy to switch to Postgres/MySQL)
- **CORS enabled**
- **OpenAPI (Swagger) Docs**

---

## 🛠 Tech Stack
- **Python 3.12**
- **FastAPI** – Web Framework
- **SQLAlchemy** – ORM
- **Pydantic** – Data Validation
- **Uvicorn** – ASGI Server
- **Passlib & python-jose** – Auth & Security
- **SQLite** (default DB)

---


# fast_api_project

# Resume-Ready FastAPI (Auth + Todos)

A clean FastAPI microservice with JWT auth, users, and todo CRUD. Great for portfolio demos.

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload



## 📂 Project Structure
fastapi-resume-api/
├── main.py # Application code
├── requirements.txt # Dependencies
├── .env.example # Example environment variables
├── README.md # Project documentation
└── app.db # SQLite database (auto-created)




---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repo
```bash
git clone https://github.com/<your-username>/fastapi-resume-api.git
cd fastapi-resume-api

2️⃣ Create & activate virtual environment
bash
Copy
Edit
python3 -m venv .venv
source .venv/bin/activate
3️⃣ Install dependencies
bash
Copy
Edit
pip install -r requirements.txt
4️⃣ Configure environment variables
bash
Copy
Edit
cp .env.example .env
# Generate secure secret
python - <<'PY'
import secrets; print("JWT_SECRET=" + secrets.token_hex(32))
PY
# Paste the generated JWT_SECRET into .env
5️⃣ Run the server
bash
Copy
Edit
uvicorn main:app --reload
Server runs at: http://127.0.0.1:8000
Swagger UI: http://127.0.0.1:8000/docs

🧪 API Usage (Quick Start)
Sign Up
http
Copy
Edit
POST /auth/signup
Content-Type: application/json
{
  "email": "you@example.com",
  "password": "secret123",
  "full_name": "John Doe"
}
Login
http
Copy
Edit
POST /auth/login
Content-Type: application/x-www-form-urlencoded
username=you@example.com&password=secret123
→ Get access_token

Authorize in Swagger
Click Authorize → Bearer <access_token>

Create Todo
http
Copy
Edit
POST /todos
Authorization: Bearer <token>
Content-Type: application/json
{
  "title": "Buy milk",
  "description": "2% fat"
}
📸 Screenshots
(Add Swagger UI screenshots here)

🚀 Deployment
Run with Docker (optional)

Deploy to Render / Railway / Azure / AWS

📜 License
This project is licensed under the MIT License.

✨ Author
Your Name
📧 you@example.com

yaml
Copy
Edit
