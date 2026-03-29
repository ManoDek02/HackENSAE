# ============================================================
#  HackENSAE — backend/routers/inscriptions.py (PostgreSQL)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
bearer = HTTPBearer(auto_error=False)

from backend.database import get_db
from backend.models.models import Inscription, Hackathon
from backend.core.security import get_current_user, require_role

router = APIRouter()

class MembreIn(BaseModel):
    nom: str
    filiere: Optional[str] = None

class InscriptionIn(BaseModel):
    hackathon_id: int
    nom_equipe: str
    email_contact: EmailStr
    membres: List[MembreIn]
    domaine: Optional[str] = None
    thematique: Optional[str] = None
    livrable_type: Optional[str] = None
    livrable_format: Optional[str] = None
    description: Optional[str] = None

class InscriptionOut(BaseModel):
    id: int
    nom_equipe: str
    statut: str
    created_at: datetime
    class Config:
        from_attributes = True

@router.post("", response_model=InscriptionOut, status_code=201)
def creer_inscription(data: InscriptionIn, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    hack = db.query(Hackathon).filter(Hackathon.id == data.hackathon_id).first()
    if not hack:
        raise HTTPException(status_code=404, detail="Hackathon introuvable.")
    if hack.statut not in ("inscriptions", "en_cours"):
        raise HTTPException(status_code=400, detail="Les inscriptions ne sont pas ouvertes.")
    nb = len([m for m in data.membres if m.nom.strip()])
    if nb > hack.taille_equipe_max:
        raise HTTPException(status_code=400,
            detail=f"Maximum {hack.taille_equipe_max} membres pour ce hackathon.")
    # Vérifier doublon équipe
    existing = db.query(Inscription).filter(
        Inscription.hackathon_id == data.hackathon_id,
        Inscription.chef_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Vous êtes déjà inscrit à ce hackathon.")

    insc = Inscription(
        hackathon_id=data.hackathon_id, chef_id=current_user.id,
        nom_equipe=data.nom_equipe.strip(), email_contact=data.email_contact,
        membres=[m.dict() for m in data.membres],
        domaine=data.domaine, thematique=data.thematique,
        livrable_type=data.livrable_type, description=data.description,
    )
    db.add(insc); db.commit(); db.refresh(insc)
    return insc

@router.get("")
def list_inscriptions(hackathon_id: Optional[int] = None,
                      db: Session = Depends(get_db),
                      credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """
    Liste les inscriptions.
    - Sans token ou token participant : retourne uniquement nom_equipe, membres (sans email)
    - Avec token organisateur/admin : retourne tout
    """
    q = db.query(Inscription)
    if hackathon_id:
        q = q.filter(Inscription.hackathon_id == hackathon_id)

    # Vérifier le rôle depuis le token si présent
    role = "public"
    if credentials:
        try:
            from backend.core.security import decode_token
            payload = decode_token(credentials.credentials)
            role = payload.get("role", "participant")
        except Exception:
            pass

    inscriptions = q.all()

    if role in ("organisateur", "admin"):
        # Tout retourner
        return [
            {
                "id": i.id, "nom_equipe": i.nom_equipe,
                "email_contact": i.email_contact,
                "membres": i.membres, "statut": i.statut,
                "domaine": i.domaine, "thematique": i.thematique,
                "hackathon_id": i.hackathon_id,
                "created_at": i.created_at,
            }
            for i in inscriptions
        ]
    else:
        # Version publique — nom équipe et nb membres seulement
        return [
            {
                "id": i.id, "nom_equipe": i.nom_equipe,
                "membres": len(i.membres) if isinstance(i.membres, list) else 0,
                "statut": i.statut,
                "domaine": i.domaine, "thematique": i.thematique,
                "hackathon_id": i.hackathon_id,
            }
            for i in inscriptions
        ]

@router.get("/me")
def my_inscriptions(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Inscription).filter(Inscription.chef_id == current_user.id).all()

@router.patch("/{inscription_id}/statut")
def changer_statut(inscription_id: int, statut: str, db: Session = Depends(get_db),
                   _=Depends(require_role("organisateur","admin"))):
    if statut not in {"en_attente","validee","refusee"}:
        raise HTTPException(status_code=400, detail="Statut invalide.")
    insc = db.query(Inscription).filter(Inscription.id == inscription_id).first()
    if not insc:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    insc.statut = statut; db.commit()
    return {"message": f"Statut mis à jour : {statut}"}
