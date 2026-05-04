# ============================================================
#  HackENSAE — Modèles SQLAlchemy (PostgreSQL)
# ============================================================

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# ── Utilisateurs ─────────────────────────────────────────────
class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id         = Column(Integer, primary_key=True, index=True)
    email      = Column(String(255), unique=True, nullable=False, index=True)
    prenom     = Column(String(100), nullable=False)
    nom        = Column(String(100), nullable=False)
    hashed_pwd = Column(String(255), nullable=False)
    role       = Column(SAEnum("participant", "organisateur", "jury", "admin",
                               name="role_enum"), default="participant")
    actif      = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    inscriptions = relationship("Inscription", back_populates="chef_equipe")
    soumissions  = relationship("Soumission",  back_populates="soumetteur")


# ── Hackathons ────────────────────────────────────────────────
class Hackathon(Base):
    __tablename__ = "hackathons"

    id              = Column(Integer, primary_key=True, index=True)
    titre           = Column(String(200), nullable=False)
    description     = Column(Text)
    organisateur    = Column(String(200))
    type            = Column(SAEnum("tech", "datajournalisme", name="type_hack_enum"))

    # Statut et phases
    statut          = Column(SAEnum(
        "a_venir", "inscriptions", "en_cours", "soumission",
        "evaluation", "termine", name="statut_hack_enum"
    ), default="a_venir")
    phase_actuelle  = Column(Integer, default=1)
    phases_total    = Column(Integer, default=6)
    phase_label     = Column(String(100), default="Communication")

    # Config équipe
    taille_equipe_min = Column(Integer, default=1)
    taille_equipe_max = Column(Integer, default=4)

    # Dates
    date_debut              = Column(DateTime)
    date_fin                = Column(DateTime)
    date_debut_inscriptions = Column(DateTime)
    date_fin_inscriptions   = Column(DateTime)
    date_soumission         = Column(DateTime)
    date_evaluation         = Column(DateTime)

    # Métadonnées flexibles (thématiques, domaines, livrables…)
    # Stockées en JSON pour supporter les deux types de hackathon
    config = Column(JSON, default=dict)
    # Exemples :
    # tech:           { "domaines": [...], "livrables": [...], "competences": [...] }
    # datajournalisme:{ "thematiques": [...], "prix": [...], "jury": [...] }

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    inscriptions = relationship("Inscription", back_populates="hackathon")
    soumissions  = relationship("Soumission",  back_populates="hackathon")


# ── Équipes / Inscriptions ────────────────────────────────────
class Inscription(Base):
    __tablename__ = "inscriptions"

    id            = Column(Integer, primary_key=True, index=True)
    hackathon_id  = Column(Integer, ForeignKey("hackathons.id"), nullable=False)
    chef_id       = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)

    nom_equipe    = Column(String(200), nullable=False)
    email_contact = Column(String(255), nullable=False)

    # Liste des membres (JSON : [{nom, filiere}, ...])
    membres       = Column(JSON, default=list)

    # Config spécifique au hackathon
    domaine       = Column(String(100))   # pour tech
    thematique    = Column(String(200))   # pour datajournalisme
    livrable_type = Column(String(50))    # article | video | vocal | prototype
    description   = Column(Text)

    statut        = Column(SAEnum(
        "en_attente", "validee", "refusee", name="statut_inscr_enum"
    ), default="en_attente")

    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relations
    hackathon   = relationship("Hackathon",     back_populates="inscriptions")
    chef_equipe = relationship("Utilisateur",   back_populates="inscriptions")
    soumission  = relationship("Soumission",    back_populates="inscription", uselist=False)


# ── Soumissions de projets ────────────────────────────────────
class Soumission(Base):
    __tablename__ = "soumissions"

    id             = Column(Integer, primary_key=True, index=True)
    hackathon_id   = Column(Integer, ForeignKey("hackathons.id"),   nullable=False)
    inscription_id = Column(Integer, ForeignKey("inscriptions.id"), nullable=False)
    soumetteur_id  = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)

    # Liens livrables
    lien_repo      = Column(String(500))   # GitHub repo (tech)
    lien_livrable  = Column(String(500))   # article/vidéo/vocal (datajournalisme)
    lien_rapport   = Column(String(500))   # PDF rapport

    # Évaluation
    note_jury      = Column(Integer)       # /100
    commentaire    = Column(Text)
    rang           = Column(Integer)

    statut         = Column(SAEnum(
        "brouillon", "soumise", "evaluee", name="statut_soum_enum"
    ), default="brouillon")

    created_at     = Column(DateTime, default=datetime.utcnow)
    updated_at     = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    hackathon   = relationship("Hackathon",    back_populates="soumissions")
    inscription = relationship("Inscription",  back_populates="soumission")
    soumetteur  = relationship("Utilisateur",  back_populates="soumissions")

# ── Messages Contact ──────────────────────────────────────────
class MessageContact(Base):
    __tablename__ = "messages_contact"

    id         = Column(Integer, primary_key=True, index=True)
    nom        = Column(String(200), nullable=False)
    email      = Column(String(255), nullable=False)
    sujet      = Column(String(150), nullable=False)
    message    = Column(Text, nullable=False)
    lu         = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
