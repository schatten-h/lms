from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets
import hashlib
from database import get_db
from models import User
from schemas import UserCreate, UserLogin

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    raw_token = request.cookies.get("session_token")
    if not raw_token:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    hashed = hash_token(raw_token)
    user = db.query(User).filter(User.session_token_hash == hashed).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Session invalide ou expirée")
    return user

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username déjà pris")
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password, role=user.role)
    db.add(new_user)
    db.commit()
    return {"msg": "Inscription réussie"}

@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Identifiants incorrects")
    
    raw_token = secrets.token_hex(32)
    db_user.session_token_hash = hash_token(raw_token)
    db.commit()
    
    response.set_cookie(key="session_token", value=raw_token, httponly=True, max_age=86400, samesite="lax")
    return {"role": db_user.role, "msg": "Connecté"}

@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.session_token_hash = None
    db.commit()
    response.delete_cookie("session_token")
    return {"msg": "Déconnecté"}

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "role": current_user.role}