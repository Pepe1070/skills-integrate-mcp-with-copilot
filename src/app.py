"""
High School Management System API

A FastAPI application for managing extracurricular activities, users, and more,
inspired by brio features.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional

# Database setup
DATABASE_URL = "sqlite:///./activities.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = "your-secret-key"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db = SessionLocal()
    if not db.query(Activity).first():
        sample_activities = [
            {"name": "Chess Club", "description": "Learn strategies and compete in chess tournaments", "schedule": "Fridays, 3:30 PM - 5:00 PM", "max_participants": 12},
            {"name": "Programming Class", "description": "Learn programming fundamentals and build software projects", "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", "max_participants": 20},
            {"name": "Gym Class", "description": "Physical education and sports activities", "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", "max_participants": 30},
            {"name": "Soccer Team", "description": "Join the school soccer team and compete in matches", "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", "max_participants": 22},
            {"name": "Basketball Team", "description": "Practice and play basketball with the school team", "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM", "max_participants": 15},
            {"name": "Art Club", "description": "Explore your creativity through painting and drawing", "schedule": "Thursdays, 3:30 PM - 5:00 PM", "max_participants": 15},
            {"name": "Drama Club", "description": "Act, direct, and produce plays and performances", "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM", "max_participants": 20},
            {"name": "Math Club", "description": "Solve challenging problems and participate in math competitions", "schedule": "Tuesdays, 3:30 PM - 4:30 PM", "max_participants": 10},
            {"name": "Debate Team", "description": "Develop public speaking and argumentation skills", "schedule": "Fridays, 4:00 PM - 5:30 PM", "max_participants": 12},
            {"name": "Science Club", "description": "Conduct experiments and explore scientific concepts", "schedule": "Wednesdays, 3:00 PM - 4:30 PM", "max_participants": 18},
            {"name": "Music Band", "description": "Learn to play instruments and perform as a band", "schedule": "Tuesdays and Thursdays, 3:00 PM - 4:00 PM", "max_participants": 25},
            {"name": "Photography Club", "description": "Capture and edit photos, learn photography techniques", "schedule": "Mondays, 4:00 PM - 5:30 PM", "max_participants": 14},
            {"name": "Robotics Team", "description": "Build and program robots for competitions", "schedule": "Fridays, 2:00 PM - 4:00 PM", "max_participants": 16},
            {"name": "Environmental Club", "description": "Promote sustainability and environmental awareness", "schedule": "Thursdays, 4:00 PM - 5:00 PM", "max_participants": 20},
            {"name": "Cooking Class", "description": "Learn cooking basics and prepare healthy meals", "schedule": "Wednesdays, 4:00 PM - 5:30 PM", "max_participants": 12},
        ]
        for act in sample_activities:
            db_activity = Activity(**act)
            db.add(db_activity)
        db.commit()
    db.close()
    yield
    # Shutdown
    pass

app = FastAPI(title="Mergington High School API",
              description="API for managing extracurricular activities with user auth",
              lifespan=lifespan)

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Database models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="student")  # student, admin

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    schedule = Column(String)
    max_participants = Column(Integer)
    participants = relationship("Registration", back_populates="activity")

class Registration(Base):
    __tablename__ = "registrations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_id = Column(Integer, ForeignKey("activities.id"))
    registered_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")
    activity = relationship("Activity", back_populates="participants")

# Pydantic models
class UserCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    role: str

class ActivityResponse(BaseModel):
    id: int
    name: str
    description: str
    schedule: str
    max_participants: int
    current_participants: int

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")

# Auth endpoints
@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, first_name=user.first_name, last_name=user.last_name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login", response_model=Token)
def login(form_data: dict, db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data["username"], form_data["password"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Activity endpoints
@app.get("/activities", response_model=List[ActivityResponse])
def get_activities(db: Session = Depends(get_db)):
    activities = db.query(Activity).options(joinedload(Activity.participants)).all()
    result = []
    for activity in activities:
        current_participants = len(activity.participants)
        result.append(ActivityResponse(
            id=activity.id,
            name=activity.name,
            description=activity.description,
            schedule=activity.schedule,
            max_participants=activity.max_participants,
            current_participants=current_participants
        ))
    return result

@app.post("/activities/{activity_id}/signup")
def signup_for_activity(activity_id: int, email: str, db: Session = Depends(get_db)):
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing = db.query(Registration).filter(Registration.user_id == user.id, Registration.activity_id == activity_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already signed up")
    
    if len(activity.participants) >= activity.max_participants:
        raise HTTPException(status_code=400, detail="Activity is full")
    
    registration = Registration(user_id=user.id, activity_id=activity_id)
    db.add(registration)
    db.commit()
    return {"message": f"Signed up {email} for {activity.name}"}

@app.delete("/activities/{activity_id}/unregister")
def unregister_from_activity(activity_id: int, email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    registration = db.query(Registration).filter(Registration.user_id == user.id, Registration.activity_id == activity_id).first()
    if not registration:
        raise HTTPException(status_code=400, detail="Not signed up")
    
    db.delete(registration)
    db.commit()
    return {"message": "Unregistered"}

