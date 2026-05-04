from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
from backend.database import get_db
from backend.models.models import MessageContact
from backend.core.security import require_role
from typing import List

router = APIRouter()

class ContactMessageIn(BaseModel):
    nom: str
    email: EmailStr
    sujet: str
    message: str

class ContactMessageOut(BaseModel):
    id: int
    nom: str
    email: str
    sujet: str
    message: str
    lu: bool
    created_at: datetime
    class Config:
        from_attributes = True

@router.post("/", response_model=ContactMessageOut, status_code=201)
def envoyer_message(data: ContactMessageIn, db: Session = Depends(get_db)):
    nouveau_message = MessageContact(
        nom=data.nom.strip(),
        email=data.email.strip(),
        sujet=data.sujet.strip(),
        message=data.message.strip()
    )
    db.add(nouveau_message)
    db.commit()
    db.refresh(nouveau_message)
    return nouveau_message

@router.get("/", response_model=List[ContactMessageOut])
def lister_messages(db: Session = Depends(get_db), _=Depends(require_role("organisateur", "admin"))):
    return db.query(MessageContact).order_by(MessageContact.created_at.desc()).all()

@router.patch("/{message_id}/lu", response_model=ContactMessageOut)
def marquer_lu(message_id: int, db: Session = Depends(get_db), _=Depends(require_role("organisateur", "admin"))):
    msg = db.query(MessageContact).filter(MessageContact.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message introuvable")
    msg.lu = not msg.lu
    db.commit()
    db.refresh(msg)
    return msg
