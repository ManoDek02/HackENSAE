# ============================================================
#  HackENSAE — backend/routers/organisateurs.py (PostgreSQL)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models.models import Hackathon, Inscription, Soumission
from backend.core.security import require_role

router = APIRouter()

@router.get("/dashboard/{hackathon_id}")
def dashboard(hackathon_id: int, db: Session = Depends(get_db),
              _=Depends(require_role("organisateur","admin"))):
    h = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Hackathon introuvable.")
    inscr_validees = db.query(Inscription).filter(
        Inscription.hackathon_id == hackathon_id, Inscription.statut=="validee").all()
    nb_inscrits = len(inscr_validees)
    nb_participants = sum(len(i.membres) if isinstance(i.membres, list) else 0 for i in inscr_validees)
    
    nb_attente = db.query(func.count(Inscription.id)).filter(
        Inscription.hackathon_id == hackathon_id, Inscription.statut=="en_attente").scalar() or 0
    nb_soum = db.query(func.count(Soumission.id)).filter(
        Soumission.hackathon_id == hackathon_id,
        Soumission.statut.in_(["soumise","evaluee"])).scalar() or 0
    nb_eval = db.query(func.count(Soumission.id)).filter(
        Soumission.hackathon_id == hackathon_id, Soumission.statut=="evaluee").scalar() or 0
    taux = round((nb_soum / nb_inscrits * 100) if nb_inscrits else 0)
    return {
        "hackathon_id": hackathon_id, "titre": h.titre,
        "phase_actuelle": h.phase_actuelle, "phase_label": h.phase_label,
        "statut": h.statut,
        "nb_inscrits": nb_inscrits, "nb_en_attente": nb_attente,
        "nb_participants": nb_participants,
        "nb_soumissions": nb_soum, "nb_evalues": nb_eval,
        "taux_completion": taux,
    }

@router.get("/classement/{hackathon_id}")
def classement(hackathon_id: int, db: Session = Depends(get_db)):
    soumissions = db.query(Soumission).filter(
        Soumission.hackathon_id == hackathon_id,
        Soumission.statut == "evaluee",
        Soumission.note_jury != None
    ).order_by(Soumission.note_jury.desc()).all()
    result = []
    for i, s in enumerate(soumissions):
        insc = db.query(Inscription).filter(Inscription.id == s.inscription_id).first()
        result.append({
            "rang": i + 1,
            "equipe": insc.nom_equipe if insc else "—",
            "note": s.note_jury,
            "commentaire": s.commentaire,
            "lien": s.lien_repo or s.lien_livrable,
            "domaine": insc.domaine if insc else None,
            "thematique": insc.thematique if insc else None,
        })
    return result
