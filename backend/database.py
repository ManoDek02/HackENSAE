# ============================================================
#  HackENSAE — backend/database.py
#  Connexion Neon PostgreSQL (serverless) via SQLAlchemy
#
#  Neon fournit deux types de connection strings :
#  1. Directe  : ep-xxx.region.aws.neon.tech         → pour migrations Alembic
#  2. Poolée   : ep-xxx-pooler.region.aws.neon.tech  → pour l'appli FastAPI
#
#  On utilise NullPool côté SQLAlchemy + la string poolée Neon (PgBouncer).
#  Cela évite les connexions "stale" quand Neon suspend le compute.
# ============================================================

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
import os
from dotenv import load_dotenv

load_dotenv()

# ── URL de connexion ──────────────────────────────────────────
# Récupère DATABASE_URL depuis .env
# Format Neon : postgresql://user:pwd@ep-xxx-pooler.region.aws.neon.tech/dbname?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Neon/Render peuvent fournir postgres:// au lieu de postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── Moteur SQLAlchemy ─────────────────────────────────────────
# On n'échoue PAS à l'import si DATABASE_URL est absente :
# la function Netlify peut démarrer et renvoyer un vrai message d'erreur.
# L'erreur est levée plus tard, au moment de la première requête DB.
if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"sslmode": "require"},
        pool_pre_ping=True,
        echo=os.getenv("DB_ECHO", "false").lower() == "true",
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None
    print("[WARNING] DATABASE_URL non définie — les routes DB seront indisponibles.")


# ── Dependency FastAPI ────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    Injecteur de session pour les routes FastAPI.

    Utilisation :
        @router.get("/")
        def liste(db: Session = Depends(get_db)):
            return db.query(Hackathon).all()
    """
    from fastapi import HTTPException
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="Base de données non configurée. Vérifiez DATABASE_URL dans les variables d'environnement Netlify."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Context manager (scripts, seeds) ─────────────────────────
@contextmanager
def get_db_ctx():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── Création des tables ───────────────────────────────────────
def create_tables():
    """Crée toutes les tables SQLAlchemy si elles n'existent pas."""
    if engine is None:
        print("[WARNING] create_tables() ignoré : DATABASE_URL non définie.")
        return
    from backend.models.models import Base
    Base.metadata.create_all(bind=engine)


# ── Test de connexion (optionnel, utile au démarrage) ─────────
def test_connection():
    if engine is None:
        print("[WARNING] test_connection() ignoré : DATABASE_URL non définie.")
        return
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Connexion Neon OK")
    except Exception as e:
        print(f"Erreur connexion Neon : {e}")
        raise