# HackENSAE — Plateforme des hackathons ENSAE Dakar

Plateforme centralisée pour le **Hackathon Tech & Data Innovation** (Club Informatique)
et le **concours Datajournalisme** (Club Presse) de l'ENSAE.

---

## Stack

| Couche      | Technologie                              |
|-------------|------------------------------------------|
| Frontend    | HTML / CSS / JS vanilla                  |
| Backend     | Python 3.11 · FastAPI                    |
| Base de données | **Neon PostgreSQL** (serverless)     |
| ORM         | SQLAlchemy 2.x · NullPool                |
| Auth        | JWT (python-jose) · bcrypt               |
| Hébergement | Render ou Railway                        |

---

## Structure

```
hackensae/
├── main.py
├── requirements.txt
├── .env.example
├── frontend/
│   ├── index.html
│   ├── css/design-system.css
│   ├── js/utils.js
│   └── pages/
│       ├── hackathon-detail.html
│       ├── inscription.html
│       ├── mon-espace.html
│       ├── dashboard-organisateur.html
│       ├── resultats.html
│       └── login.html
└── backend/
    ├── database.py          ← Connexion Neon (NullPool + sslmode=require)
    ├── core/security.py     ← JWT + bcrypt
    ├── models/models.py     ← Modèles SQLAlchemy
    └── routers/
        ├── auth.py
        ├── hackathons.py
        ├── inscriptions.py
        ├── soumissions.py
        └── organisateurs.py
```

---

## Configuration Neon

### 1. Créer le projet Neon
1. Aller sur [console.neon.tech](https://console.neon.tech)
2. Créer un nouveau projet → nommer la base `hackensae`
3. Cliquer sur **Connect** → copier les deux connection strings

### 2. Deux connection strings

Neon fournit deux URLs — **les deux sont nécessaires** :

| Type | Hostname | Usage |
|------|----------|-------|
| **Poolée** | `ep-xxx-pooler.region.aws.neon.tech` | Application FastAPI (`.env → DATABASE_URL`) |
| **Directe** | `ep-xxx.region.aws.neon.tech` | Migrations Alembic uniquement (`DATABASE_URL_DIRECT`) |

> Pourquoi deux ? La connexion poolée passe par PgBouncer (Neon) et gère le scale-to-zero.
> SQLAlchemy utilise `NullPool` pour ne pas créer son propre pool par-dessus.

### 3. Configurer .env

```bash
cp .env.example .env
```

Renseigner dans `.env` :
```
DATABASE_URL=postgresql://user:pwd@ep-xxx-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
DATABASE_URL_DIRECT=postgresql://user:pwd@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=<généré avec python -c "import secrets; print(secrets.token_hex(32))">
```

---

## Lancement local

```bash
# 1. Environnement Python
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt

# 2. Configuration
cp .env.example .env
# → Renseigner DATABASE_URL (poolée) et SECRET_KEY

# 3. Démarrer
uvicorn main:app --reload --port 8000
```

Les tables sont créées automatiquement au démarrage (`create_tables()` dans `startup`).

- Frontend : http://localhost:8000
- Docs API : http://localhost:8000/api/docs

---

## Déploiement sur Render

1. Pusher le projet sur GitHub
2. Sur Render : **New Web Service** → connecter le repo
3. **Build command** : `pip install -r requirements.txt`
4. **Start command** : `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Variables d'environnement à ajouter dans Render :
   - `DATABASE_URL` → connection string poolée Neon
   - `SECRET_KEY` → clé secrète JWT
   - `ALLOWED_ORIGINS` → URL de votre service Render

> Pas besoin de créer une base PostgreSQL sur Render — Neon s'en charge.

---

## Pages frontend

| Page | URL | Accès |
|------|-----|-------|
| Accueil | `/` | Public |
| Détail hackathon | `/pages/hackathon-detail.html?id=1` | Public |
| Inscription | `/pages/inscription.html?id=1` | Connecté |
| Mon espace | `/pages/mon-espace.html` | Participant |
| Dashboard organisateur | `/pages/dashboard-organisateur.html` | Organisateur |
| Résultats | `/pages/resultats.html` | Public |
| Connexion | `/pages/login.html` | Public |

---

## API endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/auth/register` | Créer un compte |
| POST | `/api/auth/login` | Se connecter (retourne JWT) |
| GET | `/api/hackathons` | Lister les hackathons |
| GET | `/api/hackathons/{id}` | Détail d'un hackathon |
| PATCH | `/api/hackathons/{id}/phase` | Avancer une phase (organisateur) |
| POST | `/api/inscriptions` | S'inscrire |
| GET | `/api/inscriptions` | Lister (organisateur) |
| PATCH | `/api/inscriptions/{id}/statut` | Valider/refuser (organisateur) |
| POST | `/api/soumissions` | Soumettre un projet |
| PATCH | `/api/soumissions/{id}/evaluer` | Noter (jury/organisateur) |
| GET | `/api/organisateurs/dashboard/{id}` | Métriques |
| GET | `/api/organisateurs/classement/{id}` | Classement final |
| GET | `/api/health` | Vérification état du serveur |
