from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import json

from backend.database import engine, get_db
from backend import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Orchestration Backend Service")

# URLs of microservices (use Docker service names in production, localhost for local)
import os
OCR_URL = os.getenv("OCR_URL", "http://localhost:8001/process")
EXTRACTOR_URL = os.getenv("EXTRACTOR_URL", "http://localhost:8002/extract")

# Schemas
class UserCreate(BaseModel):
    username: str
    password: str

class ProjectCreate(BaseModel):
    name: str

# Endpoints
@app.post("/auth/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    # For simplicity, not using bcrypt here, but should be used in production
    new_user = models.User(username=user.username, hashed_password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@app.post("/auth/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or db_user.hashed_password != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"user_id": db_user.id, "username": db_user.username}

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
    # Parse JSON if exists
    data = json.loads(project.extracted_data) if project.extracted_data else None
    return {"id": project.id, "name": project.name, "pdf_filename": project.pdf_filename, "extracted_data": data}

from fastapi.responses import FileResponse

@app.post("/projects/{project_id}/process")
async def process_project(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    project.pdf_filename = file.filename
    
    # Save the PDF on disk
    os.makedirs("backend/uploads", exist_ok=True)
    pdf_path = f"backend/uploads/project_{project_id}.pdf"
    with open(pdf_path, "wb") as f:
        f.write(content)
        
    db.commit()

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Call OCR Service
        ocr_response = await client.post(
            OCR_URL,
            files={"file": (file.filename, content, file.content_type)}
        )
        if ocr_response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"OCR Service failed: {ocr_response.text}")
        
        ocr_text = ocr_response.json().get("ocr_text")

        # 2. Call Extractor Service
        ext_response = await client.post(
            EXTRACTOR_URL,
            json={"ocr_text": ocr_text}
        )
        if ext_response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Extractor Service failed: {ext_response.text}")
        
        extracted_json = ext_response.json()

    # Save to database
    project.extracted_data = json.dumps(extracted_json)
    db.commit()

    return {"message": "Processing completed", "data": extracted_json}

@app.get("/projects/{project_id}/pdf")
def get_project_pdf(project_id: int):
    pdf_path = f"backend/uploads/project_{project_id}.pdf"
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(pdf_path, media_type="application/pdf")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
