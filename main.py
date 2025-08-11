import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (Column, Integer, String, Boolean, ForeignKey, Text,
                        create_engine, func)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from dotenv import load_dotenv

# -----------------------------------------------------------------------------
# Env & config
# -----------------------------------------------------------------------------
load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "dev-super-secret-change-me")
JWT_ALGO = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "60"))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# -----------------------------------------------------------------------------
# DB setup (SQLAlchemy 2.0 style engine, classic ORM for simplicity)
# -----------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    full_name = Column(String(120), default="")
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(String(30), default=lambda: datetime.utcnow().isoformat())

    todos = relationship("Todo", back_populates="owner", cascade="all, delete-orphan")


class Todo(Base):
    __tablename__ = "todos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, default="")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(String(30), default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String(30), default=lambda: datetime.utcnow().isoformat())

    owner = relationship("User", back_populates="todos")

# -----------------------------------------------------------------------------
# Schemas
# -----------------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = ""


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = ""


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None


class TodoOut(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# -----------------------------------------------------------------------------
# Auth utils
# -----------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_minutes: int = JWT_EXPIRES_MIN) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGO)

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
tags_metadata = [
    {"name": "auth", "description": "Sign up & login to get a JWT."},
    {"name": "users", "description": "User profile endpoints."},
    {"name": "todos", "description": "CRUD for your personal todos."},
]

app = FastAPI(
    title="Resume-Ready FastAPI (Auth + Todos)",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_error
    return user

# -----------------------------------------------------------------------------
# Startup
# -----------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------------
# Routes: health
# -----------------------------------------------------------------------------
@app.get("/", summary="Service health")
def root():
    return {"status": "ok", "service": "resume-ready-fastapi"}

# -----------------------------------------------------------------------------
# Routes: auth
# -----------------------------------------------------------------------------
@app.post("/auth/signup", response_model=UserOut, tags=["auth"], status_code=201)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name or "",
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm has fields: username, password
    user = db.query(User).filter(func.lower(User.email) == form.username.lower()).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

# -----------------------------------------------------------------------------
# Routes: users
# -----------------------------------------------------------------------------
@app.get("/me", response_model=UserOut, tags=["users"])
def me(current_user: User = Depends(get_current_user)):
    return current_user

# -----------------------------------------------------------------------------
# Routes: todos
# -----------------------------------------------------------------------------
@app.post("/todos", response_model=TodoOut, tags=["todos"], status_code=201)
def create_todo(
    payload: TodoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = Todo(
        title=payload.title,
        description=payload.description or "",
        owner_id=current_user.id,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@app.get("/todos", response_model=List[TodoOut], tags=["todos"])
def list_todos(
    q: Optional[str] = Query(default=None, description="Search in title/description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Todo).filter(Todo.owner_id == current_user.id)
    if q:
        like = f"%{q}%"
        query = query.filter((Todo.title.ilike(like)) | (Todo.description.ilike(like)))
    items = query.order_by(Todo.id.desc()).offset(skip).limit(limit).all()
    return items


@app.get("/todos/{todo_id}", response_model=TodoOut, tags=["todos"])
def get_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = db.get(Todo, todo_id)
    if not todo or todo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@app.put("/todos/{todo_id}", response_model=TodoOut, tags=["todos"])
def update_todo(
    todo_id: int,
    payload: TodoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = db.get(Todo, todo_id)
    if not todo or todo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
    if payload.title is not None:
        todo.title = payload.title
    if payload.description is not None:
        todo.description = payload.description
    todo.updated_at = datetime.utcnow().isoformat()
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}", status_code=204, tags=["todos"])
def delete_todo(
    todo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    todo = db.get(Todo, todo_id)
    if not todo or todo.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return None
