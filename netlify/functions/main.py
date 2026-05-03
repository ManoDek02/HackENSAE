import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import os
from mangum import Mangum

# Import de tes modules existants
from backend.database import create_tables
from backend.routers import hackathons, inscriptions, auth, soumissions, organisateurs

# Initialisation simplifiée pour le Serverless
app = FastAPI(
    title="HackENSAE API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# L'adaptateur Mangum doit être défini ici
handler = Mangum(app)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(auth.router,           prefix="/api/auth",          tags=["Auth"])
app.include_router(hackathons.router,    prefix="/api/hackathons",    tags=["Hackathons"])
app.include_router(inscriptions.router,  prefix="/api/inscriptions",  tags=["Inscriptions"])
app.include_router(soumissions.router,   prefix="/api/soumissions",   tags=["Soumissions"])
app.include_router(organisateurs.router, prefix="/api/organisateurs", tags=["Organisateurs"])

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "HackENSAE"}

# --- GESTION DU FRONTEND ---
FRONTEND = Path(__file__).parent / "frontend"

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = FRONTEND / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"error": "Frontend non trouvé"}

# Montage des fichiers statiques (CSS, JS, Pages)
# Note : Sur Netlify, il est souvent préférable de laisser Netlify servir le statique, 
# mais ceci permet de garder la logique FastAPI intacte.
if FRONTEND.exists():
    app.mount("/css",   StaticFiles(directory=str(FRONTEND / "css")),   name="css")
    app.mount("/js",    StaticFiles(directory=str(FRONTEND / "js")),    name="js")
    app.mount("/pages", StaticFiles(directory=str(FRONTEND / "pages")), name="pages")