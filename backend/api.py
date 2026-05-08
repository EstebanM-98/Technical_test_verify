import json
import os
import logging

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import engine, get_db
from backend import models
from backend.schemas import UserCreate, ProjectCreate, ProjectUpdate
from backend.security import hash_password, verify_password
from backend.services import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Orchestration Backend Service")

UPLOADS_DIR = "/app/data/uploads"


# ─── Auth ────────────────────────────────────────────────────────────────────

@app.post("/auth/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = models.User(
        username=user.username,
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User registered successfully"}


@app.post("/auth/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"user_id": db_user.id, "username": db_user.username}


# ─── Projects ────────────────────────────────────────────────────────────────

@app.post("/projects")
def create_project(project: ProjectCreate, user_id: int, db: Session = Depends(get_db)):
    new_project = models.Project(name=project.name, owner_id=user_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


@app.get("/projects")
def get_projects(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Project).filter(models.Project.owner_id == user_id).all()


@app.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    data = json.loads(project.extracted_data) if project.extracted_data else None
    return {
        "id": project.id,
        "name": project.name,
        "pdf_filename": project.pdf_filename,
        "extracted_data": data,
    }


@app.put("/projects/{project_id}")
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = project_update.name
    db.commit()
    db.refresh(project)
    return project


@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    pdf_path = os.path.join(UPLOADS_DIR, f"project_{project_id}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}


@app.post("/projects/{project_id}/process")
async def process_project(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    project.pdf_filename = file.filename

    os.makedirs(UPLOADS_DIR, exist_ok=True)
    pdf_path = os.path.join(UPLOADS_DIR, f"project_{project_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(content)
    db.commit()

    try:
        extracted_json = await run_pipeline(file.filename, content)
    except RuntimeError as e:
        logger.error(f"Pipeline failed for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    project.extracted_data = json.dumps(extracted_json)
    db.commit()
    return {"message": "Processing completed", "data": extracted_json}


@app.get("/projects/{project_id}/pdf")
def get_project_pdf(project_id: int):
    pdf_path = os.path.join(UPLOADS_DIR, f"project_{project_id}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type="application/pdf")
