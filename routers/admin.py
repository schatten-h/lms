from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, Module, Certificate
from routers.auth import get_current_user
from schemas import ModuleCreate, IssueCertificate

router = APIRouter()

@router.post("/modules")
def create_module(mod: ModuleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "admin": raise HTTPException(status_code=403, detail="Accès refusé")
    new_mod = Module(title=mod.title, description=mod.description)
    db.add(new_mod)
    db.commit()
    return {"msg": "Module créé"}

@router.post("/certificates")
def issue_cert(cert: IssueCertificate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "admin": raise HTTPException(status_code=403, detail="Accès refusé")
    c = Certificate(student_id=cert.student_id, module_id=cert.module_id)
    db.add(c)
    db.commit()
    return {"msg": "Certificat délivré"}


@router.get("/modules")
def list_modules(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.role != "admin": raise HTTPException(status_code=403, detail="Accès refusé")
    mods = db.query(Module).all()
    return [{"id": m.id, "title": m.title, "description": m.description} for m in mods]