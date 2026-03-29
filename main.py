from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import os

from backend.database import create_tables
from backend.routers import hackathons, inscriptions, auth, soumissions, organisateurs

app = FastAPI(
    title="HackENSAE API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers API en premier ───────────────────────────────────
app.include_router(auth.router,          prefix="/api/auth",          tags=["Auth"])
app.include_router(hackathons.router,    prefix="/api/hackathons",    tags=["Hackathons"])
app.include_router(inscriptions.router,  prefix="/api/inscriptions",  tags=["Inscriptions"])
app.include_router(soumissions.router,   prefix="/api/soumissions",   tags=["Soumissions"])
app.include_router(organisateurs.router, prefix="/api/organisateurs", tags=["Organisateurs"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "HackENSAE"}

@app.on_event("startup")
async def startup():
    create_tables()

# ── Pages HTML ───────────────────────────────────────────────
FRONTEND = Path("frontend")

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(str(FRONTEND / "index.html"))

@app.get("/index.html", response_class=HTMLResponse)
async def index():
    return FileResponse(str(FRONTEND / "index.html"))

# ── Fichiers statiques APRÈS les routes API ──────────────────
if FRONTEND.exists():
    app.mount("/css",   StaticFiles(directory=str(FRONTEND / "css")),   name="css")
    app.mount("/js",    StaticFiles(directory=str(FRONTEND / "js")),    name="js")
    app.mount("/pages", StaticFiles(directory=str(FRONTEND / "pages")), name="pages")