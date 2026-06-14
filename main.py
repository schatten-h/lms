import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from database import engine, Base

# Importation de tes routeurs
from routers import auth, admin, teacher, student

# Création automatique des tables dans ta base de données Neon
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LMS API - Application Complète")

# Création des dossiers d'upload s'ils n'existent pas encore
os.makedirs(os.path.join("uploads", "pdfs"), exist_ok=True)
os.makedirs(os.path.join("uploads", "videos"), exist_ok=True)

# Montage du dossier 'static' pour que tes pages HTML puissent charger le CSS et le JS
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    pass # Ignore si le dossier /static n'est pas encore créé au lancement

# Montage du dossier 'uploads' pour pouvoir lire les PDF et Vidéos
try:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except RuntimeError:
    pass

# 1. ROUTES BACKEND (API)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentification"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(teacher.router, prefix="/api/teacher", tags=["Enseignant"])
app.include_router(student.router, prefix="/api/student", tags=["Étudiant"]) 


# 2. ROUTES FRONTEND (PAGES HTML)


@app.get("/", response_class=FileResponse, tags=["Pages"])
def home_page(): 
    # Par défaut, quand on arrive sur le site, on affiche la page de connexion
    return "static/login.html"

@app.get("/login", response_class=FileResponse, tags=["Pages"])
def login_page():
    return "static/login.html"

@app.get("/register", response_class=FileResponse, tags=["Pages"])
def register_page():
    return "static/register.html"

@app.get("/admin", response_class=FileResponse, tags=["Pages"])
def admin_page():
    return "static/admin.html"

@app.get("/enseignant", response_class=FileResponse, tags=["Pages"])
def teacher_page():
    return "static/enseignant.html"

@app.get("/etudiant", response_class=FileResponse, tags=["Pages"])
def student_page():
    return "static/etudiant.html"

@app.get("/lesson", response_class=FileResponse, tags=["Pages"])
def lesson_page():
    return "static/lesson.html"

@app.get("/certificate", response_class=FileResponse, tags=["Pages"])
def certificate_page():
    return "static/certificate.html"