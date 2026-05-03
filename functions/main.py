import sys
import os

# ── Résolution du chemin ──────────────────────────────────────
# Sur Netlify Functions (AWS Lambda), tous les fichiers inclus
# via "included_files" sont déployés dans le même répertoire
# que main.py (/var/task/).
# On ajoute donc le dossier courant ET le parent en fallback
# (pour le développement local où backend/ est au niveau racine).
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.abspath(os.path.join(_here, ".."))

if _here not in sys.path:
    sys.path.insert(0, _here)   # /var/task/ sur Netlify (backend/ y est copié)
if _root not in sys.path:
    sys.path.insert(1, _root)   # racine du projet en local

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from backend.database import create_tables
from backend.routers import hackathons, inscriptions, auth, soumissions, organisateurs

# ── Application FastAPI ───────────────────────────────────────
app = FastAPI(
    title="HackENSAE API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes API ────────────────────────────────────────────────
app.include_router(auth.router,           prefix="/api/auth",          tags=["Auth"])
app.include_router(hackathons.router,     prefix="/api/hackathons",    tags=["Hackathons"])
app.include_router(inscriptions.router,   prefix="/api/inscriptions",  tags=["Inscriptions"])
app.include_router(soumissions.router,    prefix="/api/soumissions",   tags=["Soumissions"])
app.include_router(organisateurs.router,  prefix="/api/organisateurs", tags=["Organisateurs"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "HackENSAE"}


@app.on_event("startup")
async def startup():
    try:
        create_tables()
    except Exception as e:
        print(f"[startup] Erreur création tables : {e}")


# ── Adaptateur Mangum ─────────────────────────────────────────
# Instancié EN DERNIER — après toute la configuration de l'app.
handler = Mangum(app, lifespan="off")