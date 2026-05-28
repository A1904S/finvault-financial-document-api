from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import hashlib
import secrets
from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# hashing password - i used hashlib bcoz bcrypt was giving error
def hash_password(password: str) -> str:
    salt = secrets.token_hex(32)
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(plain: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split(":")
        return hashlib.sha256((salt + plain).encode()).hexdigest() == hashed
    except:
        return False

@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserRegister, db: Session = Depends(get_db)):
    # check if email already exists
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="email already exists")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="username taken")

    new_user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        company_name=data.company_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="wrong username or password")
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="wrong username or password")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
