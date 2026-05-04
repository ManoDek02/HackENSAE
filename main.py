import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

# Initialisation
from backend.database import create_tables
from backend.routers import hackathons, inscriptions, auth, soumissions, organisateurs, contact

app = FastAPI(
    title="HackENSAE API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes API
app.include_router(auth.router,           prefix="/api/auth",          tags=["Auth"])
app.include_router(hackathons.router,     prefix="/api/hackathons",    tags=["Hackathons"])
app.include_router(inscriptions.router,   prefix="/api/inscriptions",  tags=["Inscriptions"])
app.include_router(soumissions.router,    prefix="/api/soumissions",   tags=["Soumissions"])
app.include_router(organisateurs.router,  prefix="/api/organisateurs", tags=["Organisateurs"])
app.include_router(contact.router,        prefix="/api/contact",       tags=["Contact"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "HackENSAE"}

@app.on_event("startup")
async def startup():
    try:
        create_tables()
    except Exception as e:
        print(f"[startup] Erreur création tables : {e}")

# --- GESTION DU FRONTEND ---
FRONTEND = Path(__file__).parent / "frontend"

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = FRONTEND / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Frontend non trouvé"}

# Montage des fichiers statiques (CSS, JS, Pages)
if FRONTEND.exists():
    app.mount("/css",   StaticFiles(directory=str(FRONTEND / "css")),   name="css")
    app.mount("/js",    StaticFiles(directory=str(FRONTEND / "js")),    name="js")
    app.mount("/pages", StaticFiles(directory=str(FRONTEND / "pages")), name="pages")

# Si on accède à n'importe quelle autre route non-API, on renvoie vers index.html (pour la navigation SPA si besoin)
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    if not request.url.path.startswith("/api/"):
        index_path = FRONTEND / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    from fastapi.responses import JSONResponse
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
