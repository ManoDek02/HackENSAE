# ============================================================
#  HackENSAE — backend/routers/auth.py  (version PostgreSQL)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import os

from backend.database import get_db
from backend.models.models import Utilisateur
from backend.core.security import hash_password, verify_password, create_access_token

router = APIRouter()

class RegisterIn(BaseModel):
    email: EmailStr
    prenom: str
    nom: str
    password: str
    role: Optional[str] = "participant"
    organizer_code: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    prenom: str
    nom: str
    role: str
    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

@router.post("/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(Utilisateur).filter(Utilisateur.email == data.email).first():
        raise HTTPException(status_code=409, detail="Cet email est déjà utilisé.")
    ORGANIZER_CODE = os.getenv("ORGANIZER_CODE", "")

    if data.role == "organisateur":
        code_fourni = getattr(data, 'organizer_code', '')
        if not ORGANIZER_CODE or code_fourni != ORGANIZER_CODE:
            role = "participant"  # refuse silencieusement sans révéler le code
        else:
            role = "organisateur"
    else:
        role = "participant"
    user = Utilisateur(email=data.email, prenom=data.prenom.strip(), nom=data.nom.strip(),
                       hashed_pwd=hash_password(data.password), role=role)
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role,
                                  "email": user.email, "prenom": user.prenom, "nom": user.nom})
    return TokenOut(access_token=token, user=UserOut.from_orm(user))

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(Utilisateur).filter(Utilisateur.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_pwd):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    if not user.actif:
        raise HTTPException(status_code=403, detail="Compte désactivé.")
    token = create_access_token({"sub": str(user.id), "role": user.role,
                                  "email": user.email, "prenom": user.prenom, "nom": user.nom})
    return TokenOut(access_token=token, user=UserOut.from_orm(user))

@router.get("/me", response_model=UserOut)
def me(user: Utilisateur = Depends(lambda: None)):
    """Exemple — injecter get_current_user depuis security.py"""
    raise HTTPException(status_code=501, detail="Utiliser Depends(get_current_user).")
