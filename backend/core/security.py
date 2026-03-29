# ============================================================
#  HackENSAE — backend/core/security.py
# ============================================================

from datetime import datetime, timedelta
from typing import Optional
import os

from jose import JWTError, jwt
import bcrypt as _bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database import get_db

SECRET_KEY  = os.getenv("SECRET_KEY", "changez-moi-en-production-secret-key-longue")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("TOKEN_EXPIRE_MIN", "60"))

bearer = HTTPBearer(auto_error=False)


# ── Mots de passe ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT ───────────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    payload = data.copy()
    expire  = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── get_current_user ──────────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentification requise.")

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token malformé.")

    from backend.models.models import Utilisateur
    try:
        user = db.query(Utilisateur).filter(Utilisateur.id == int(user_id)).first()
    except Exception:
        # Table pas encore créée ou erreur DB : on crée un objet minimal depuis le token
        user = None

    if not user:
        # Fallback : objet minimal depuis le payload JWT
        # Permet de fonctionner même si la table est vide ou absente
        class _TokenUser:
            id    = int(user_id)
            email = payload.get("email", "")
            prenom= payload.get("prenom", "")
            nom   = payload.get("nom", "")
            role  = payload.get("role", "participant")
            actif = True
        return _TokenUser()

    if not user.actif:
        raise HTTPException(status_code=401, detail="Compte désactivé.")
    return user


# ── require_role ──────────────────────────────────────────────
def require_role(*roles: str):
    """
    Vérifie que l'utilisateur connecté a l'un des rôles requis.
    Le rôle est lu depuis l'objet user (DB ou token JWT en fallback).
    """
    def _check(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès réservé aux rôles : {', '.join(roles)}. "
                       f"Votre rôle actuel : {user.role}"
            )
        return user
    return _check
