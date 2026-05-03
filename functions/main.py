import sys
import os

# ── Chemin vers la racine du projet ──────────────────────────
# functions/main.py est dans functions/, le projet est à ../
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

# ── CORS — DOIT être ajouté avant Mangum ─────────────────────
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


# ── Création des tables au premier démarrage ──────────────────
@app.on_event("startup")
async def startup():
    try:
        create_tables()
    except Exception as e:
        print(f"[startup] Erreur création tables : {e}")


# ── Adaptateur Mangum ─────────────────────────────────────────
# Instancié EN DERNIER, après toute la configuration de l'app.
# lifespan="off" est nécessaire pour les fonctions serverless
# (Netlify Functions ne supporte pas les lifespans ASGI).
handler = Mangum(app, lifespan="off")