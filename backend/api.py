import json
import os
import time

from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import engine, get_db
from backend import models
from backend.schemas import UserCreate, ProjectCreate, ProjectUpdate
from backend.security import hash_password, verify_password
from backend.services import run_pipeline
from logger import get_logger

logger = get_logger(__name__, "backend.log")

models.Base.metadata.create_all(bind=engine)
logger.info("Database tables verified/created on startup.")

app = FastAPI(title="Orchestration Backend Service")

UPLOADS_DIR = "/app/data/uploads"


# ─── Auth ────────────────────────────────────────────────────────────────────

@app.post("/auth/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    logger.info("Registration attempt for username='%s'", user.username)
    if db.query(models.User).filter(models.User.username == user.username).first():
        logger.warning("Registration failed: username='%s' already exists.", user.username)
        raise HTTPException(status_code=400, detail="Username already registered")
    db_user = models.User(
        username=user.username,
        hashed_password=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info("User registered successfully: username='%s', id=%s", db_user.username, db_user.id)
    return {"message": "User registered successfully"}


@app.post("/auth/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    logger.info("Login attempt for username='%s'", user.username)
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        logger.warning("Login failed: invalid credentials for username='%s'", user.username)
        raise HTTPException(status_code=400, detail="Invalid credentials")
    logger.info("Login successful: username='%s', id=%s", db_user.username, db_user.id)
    return {"user_id": db_user.id, "username": db_user.username}


# ─── Projects ────────────────────────────────────────────────────────────────

@app.post("/projects")
def create_project(project: ProjectCreate, user_id: int, db: Session = Depends(get_db)):
    logger.info("Creating project name='%s' for user_id=%s", project.name, user_id)
    new_project = models.Project(name=project.name, owner_id=user_id)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    logger.info("Project created: id=%s, name='%s', owner_id=%s", new_project.id, new_project.name, user_id)
    return new_project


@app.get("/projects")
def get_projects(user_id: int, db: Session = Depends(get_db)):
    logger.debug("Fetching all projects for user_id=%s", user_id)
    projects = db.query(models.Project).filter(models.Project.owner_id == user_id).all()
    logger.info("Returning %d project(s) for user_id=%s", len(projects), user_id)
    return projects


@app.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)):
    logger.debug("Fetching project_id=%s", project_id)
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.warning("Project not found: project_id=%s", project_id)
        raise HTTPException(status_code=404, detail="Project not found")
    data = json.loads(project.extracted_data) if project.extracted_data else None
    logger.debug("Project fetched: project_id=%s, has_data=%s", project_id, data is not None)
    return {
        "id": project.id,
        "name": project.name,
        "pdf_filename": project.pdf_filename,
        "extracted_data": data,
    }


@app.put("/projects/{project_id}")
def update_project(project_id: int, project_update: ProjectUpdate, db: Session = Depends(get_db)):
    logger.info("Updating project_id=%s with new name='%s'", project_id, project_update.name)
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.warning("Update failed: project_id=%s not found.", project_id)
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = project_update.name
    db.commit()
    db.refresh(project)
    logger.info("Project updated successfully: project_id=%s", project_id)
    return project


@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    logger.info("Delete requested for project_id=%s", project_id)
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.warning("Delete failed: project_id=%s not found.", project_id)
        raise HTTPException(status_code=404, detail="Project not found")
    pdf_path = os.path.join(UPLOADS_DIR, f"project_{project_id}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
        logger.debug("Deleted PDF file: %s", pdf_path)
    db.delete(project)
    db.commit()
    logger.info("Project deleted: project_id=%s", project_id)
    return {"message": "Project deleted successfully"}


@app.post("/projects/{project_id}/process")
async def process_project(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    logger.info(
        "Processing started: project_id=%s, filename='%s', content_type='%s'",
        project_id, file.filename, file.content_type,
    )
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        logger.warning("Process failed: project_id=%s not found.", project_id)
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    logger.debug("File read into memory: %d bytes", len(content))

    project.pdf_filename = file.filename
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    pdf_path = os.path.join(UPLOADS_DIR, f"project_{project_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(content)
    db.commit()
    logger.debug("PDF saved to disk: %s", pdf_path)

    start_time = time.perf_counter()
    try:
        extracted_json = await run_pipeline(file.filename, content)
    except RuntimeError as e:
        logger.error(
            "Pipeline failed for project_id=%s after %.2fs: %s",
            project_id, time.perf_counter() - start_time, e,
        )
        raise HTTPException(status_code=500, detail=str(e))

    elapsed = time.perf_counter() - start_time
    logger.info("Pipeline completed for project_id=%s in %.2fs", project_id, elapsed)

    project.extracted_data = json.dumps(extracted_json)
    db.commit()
    return {"message": "Processing completed", "data": extracted_json}


@app.get("/projects/{project_id}/pdf")
def get_project_pdf(project_id: int):
    pdf_path = os.path.join(UPLOADS_DIR, f"project_{project_id}.pdf")
    logger.debug("PDF requested for project_id=%s, path=%s", project_id, pdf_path)
    if not os.path.exists(pdf_path):
        logger.warning("PDF not found for project_id=%s at path=%s", project_id, pdf_path)
        raise HTTPException(status_code=404, detail="PDF not found")
    logger.debug("Serving PDF for project_id=%s", project_id)
    return FileResponse(pdf_path, media_type="application/pdf")
