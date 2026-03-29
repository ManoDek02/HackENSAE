# ============================================================
#  HackENSAE — backend/routers/hackathons.py
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from backend.database import get_db
from backend.models.models import Hackathon, Inscription
from backend.core.security import require_role, get_current_user

router = APIRouter(redirect_slashes=False)

# ── Schémas ───────────────────────────────────────────────────
class HackathonCreate(BaseModel):
    titre: str
    type: str                          # "tech" | "datajournalisme"
    organisateur: Optional[str] = None
    description: Optional[str] = None
    taille_equipe_min: int = 1
    taille_equipe_max: int = 4
    date_debut_inscriptions: Optional[datetime] = None
    date_fin_inscriptions:   Optional[datetime] = None
    date_debut:              Optional[datetime] = None
    date_fin:                Optional[datetime] = None
    date_soumission:         Optional[datetime] = None
    date_evaluation:         Optional[datetime] = None
    config: dict = {}
    # config contient : domaines, thematiques, livrables, regles, prix, jury, competences, phases


# ── Routes statiques AVANT /{id} ─────────────────────────────
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    from backend.models.models import Soumission
    nb_hacks   = db.query(func.count(Hackathon.id)).scalar() or 0
    nb_equipes = db.query(func.count(Inscription.id)).filter(Inscription.statut=="validee").scalar() or 0
    nb_projets = db.query(func.count(Soumission.id)).filter(Soumission.statut.in_(["soumise","evaluee"])).scalar() or 0
    return {"hackathons": nb_hacks, "equipes": nb_equipes,
            "participants": nb_equipes * 3, "projets": nb_projets}


# ── CRUD ──────────────────────────────────────────────────────
@router.get("", response_model=List[dict])
def list_hackathons(statut: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(Hackathon)
    if statut:
        q = q.filter(Hackathon.statut == statut)
    result = []
    for h in q.all():
        nb  = db.query(func.count(Inscription.id)).filter(
              Inscription.hackathon_id == h.id, Inscription.statut=="validee").scalar() or 0
        cfg = h.config or {}
        domaines = cfg.get("domaines", cfg.get("thematiques", []))[:4]
        result.append({
            "id": h.id, "titre": h.titre, "organisateur": h.organisateur,
            "type": h.type, "statut": h.statut,
            "phase_actuelle": h.phase_actuelle, "phases_total": h.phases_total,
            "phase_label": h.phase_label,
            "taille_equipe_min": h.taille_equipe_min, "taille_equipe_max": h.taille_equipe_max,
            "date_fin_inscriptions": h.date_fin_inscriptions,
            "nb_equipes_inscrites": nb, "domaines": domaines,
            "description": h.description,
        })
    return result


@router.post("", status_code=201)
def create_hackathon(data: HackathonCreate, db: Session = Depends(get_db),
                     _=Depends(require_role("organisateur","admin"))):
    phases_tech  = ["Communication","Inscriptions","Formation","Développement","Soumission","Évaluation"]
    phases_dataj = ["Communication","Lancement","Production","Soumission","Évaluation"]
    phases_total = 6 if data.type == "tech" else 5

    h = Hackathon(
        titre=data.titre, type=data.type,
        organisateur=data.organisateur, description=data.description,
        statut="a_venir", phase_actuelle=1,
        phases_total=phases_total,
        phase_label=(phases_tech if data.type=="tech" else phases_dataj)[0],
        taille_equipe_min=data.taille_equipe_min,
        taille_equipe_max=data.taille_equipe_max,
        date_debut=data.date_debut,
        date_fin=data.date_fin,
        date_debut_inscriptions=data.date_debut_inscriptions,
        date_fin_inscriptions=data.date_fin_inscriptions,
        date_soumission=data.date_soumission,
        date_evaluation=data.date_evaluation,
        config=data.config,
    )
    db.add(h); db.commit(); db.refresh(h)
    return h


@router.get("/{hackathon_id}")
def get_hackathon(hackathon_id: int, db: Session = Depends(get_db)):
    h = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hackathon introuvable.")
    nb  = db.query(func.count(Inscription.id)).filter(
          Inscription.hackathon_id == h.id, Inscription.statut=="validee").scalar() or 0
    nb_soum = db.query(func.count()).select_from(
        __import__('backend.models.models', fromlist=['Soumission']).Soumission
    ).filter_by(hackathon_id=h.id).scalar() or 0
    cfg = h.config or {}
    return {
        **{c.name: getattr(h, c.name) for c in h.__table__.columns},
        "nb_equipes_inscrites": nb,
        "nb_soumissions": nb_soum,
        "domaines": cfg.get("domaines", cfg.get("thematiques", []))[:4],
    }


@router.put("/{hackathon_id}")
def update_hackathon(hackathon_id: int, data: HackathonCreate,
                     db: Session = Depends(get_db),
                     _=Depends(require_role("organisateur","admin"))):
    h = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hackathon introuvable.")
    for field, val in data.dict(exclude_unset=True).items():
        setattr(h, field, val)
    db.commit(); db.refresh(h)
    return h


@router.patch("/{hackathon_id}/phase")
def avancer_phase(hackathon_id: int, nouvelle_phase: int,
                  db: Session = Depends(get_db),
                  _=Depends(require_role("organisateur","admin"))):
    h = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hackathon introuvable.")
    phases_tech  = ["Communication","Inscriptions","Formation","Développement","Soumission","Évaluation"]
    phases_dataj = ["Communication","Lancement","Production","Soumission","Évaluation"]
    phases  = phases_tech if h.type=="tech" else phases_dataj
    if not 1 <= nouvelle_phase <= len(phases):
        raise HTTPException(status_code=400, detail="Phase invalide.")
    statuts_tech  = {1:"a_venir",2:"inscriptions",3:"en_cours",4:"en_cours",5:"soumission",6:"evaluation"}
    statuts_dataj = {1:"a_venir",2:"inscriptions",3:"en_cours",4:"soumission",5:"evaluation"}
    mapping = statuts_tech if h.type=="tech" else statuts_dataj
    h.phase_actuelle = nouvelle_phase
    h.phase_label    = phases[nouvelle_phase-1]
    h.statut         = mapping.get(nouvelle_phase,"en_cours")
    db.commit(); db.refresh(h)
    return {"message": f"Phase : {h.phase_label}", "statut": h.statut,
            "phase_actuelle": h.phase_actuelle}


@router.delete("/{hackathon_id}", status_code=204)
def delete_hackathon(hackathon_id: int, db: Session = Depends(get_db),
                     _=Depends(require_role("admin"))):
    h = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hackathon introuvable.")
    db.delete(h); db.commit()
