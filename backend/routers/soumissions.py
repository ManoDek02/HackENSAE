# ============================================================
#  HackENSAE — backend/routers/soumissions.py (PostgreSQL)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.database import get_db
from backend.models.models import Soumission, Inscription, Hackathon
from backend.core.security import get_current_user, require_role

router = APIRouter()

class SoumissionIn(BaseModel):
    hackathon_id: int
    inscription_id: int
    lien_repo: Optional[str] = None
    lien_livrable: Optional[str] = None
    lien_rapport: Optional[str] = None

class EvaluationIn(BaseModel):
    note: int
    commentaire: Optional[str] = None
    rang: Optional[int] = None

@router.post("", status_code=201)
def soumettre(data: SoumissionIn, db: Session = Depends(get_db),
              current_user=Depends(get_current_user)):
    if not data.lien_repo and not data.lien_livrable:
        raise HTTPException(status_code=422, detail="Un lien de livrable est requis.")
    insc = db.query(Inscription).filter(
        Inscription.id == data.inscription_id,
        Inscription.chef_id == current_user.id
    ).first()
    if not insc:
        raise HTTPException(status_code=403, detail="Inscription introuvable ou non autorisée.")

    # Vérification que le hackathon est bien en phase de soumission
    hack = db.query(Hackathon).filter(Hackathon.id == data.hackathon_id).first()
    if not hack or hack.statut != "soumission":
        raise HTTPException(status_code=403, detail="La phase de soumission n'est pas ouverte pour ce hackathon.")
    existing = db.query(Soumission).filter(Soumission.inscription_id == data.inscription_id).first()
    if existing:
        existing.lien_repo = data.lien_repo or existing.lien_repo
        existing.lien_livrable = data.lien_livrable or existing.lien_livrable
        existing.lien_rapport = data.lien_rapport or existing.lien_rapport
        existing.statut = "soumise"
        db.commit(); db.refresh(existing)
        return existing
    s = Soumission(hackathon_id=data.hackathon_id, inscription_id=data.inscription_id,
                   soumetteur_id=current_user.id, lien_repo=data.lien_repo,
                   lien_livrable=data.lien_livrable, lien_rapport=data.lien_rapport,
                   statut="soumise")
    db.add(s); db.commit(); db.refresh(s)
    return s

@router.get("")
def list_soumissions(hackathon_id: Optional[int] = None, db: Session = Depends(get_db),
                     _=Depends(require_role("organisateur","jury","admin"))):
    q = db.query(Soumission)
    if hackathon_id:
        q = q.filter(Soumission.hackathon_id == hackathon_id)
    return q.all()

@router.patch("/{soumission_id}/evaluer")
def evaluer(soumission_id: int, data: EvaluationIn, db: Session = Depends(get_db),
            _=Depends(require_role("organisateur","jury","admin"))):
    if not 0 <= data.note <= 100:
        raise HTTPException(status_code=400, detail="Note entre 0 et 100.")
    s = db.query(Soumission).filter(Soumission.id == soumission_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Soumission introuvable.")
    s.note_jury = data.note; s.commentaire = data.commentaire
    s.rang = data.rang; s.statut = "evaluee"
    db.commit(); db.refresh(s)
    return s
