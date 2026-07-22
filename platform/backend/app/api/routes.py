from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from pathlib import Path
from typing import Dict
from uuid import uuid4
from ..services.analyzer_service import AnalyzerService
from ..db import SessionLocal
from sqlalchemy.orm import Session
from .. import models
from .auth import get_db

router = APIRouter()


# simple in-memory store for demo MVP
_reports: Dict[str, dict] = {}


class AnalyzeRequest(BaseModel):
    project_id: int | None = None
    path: str = "."


@router.post("/projects")
def create_project(name: str, path: str, db: Session = Depends(get_db)):
    proj = models.Project(name=name, root_path=path)
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return {"id": proj.id, "name": proj.name, "root_path": proj.root_path}


@router.post("/analyze")
def analyze(req: AnalyzeRequest, db: Session = Depends(get_db)):
    path = Path(req.path)
    if not path.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")

    job_id = uuid4().hex
    service = AnalyzerService(root=path)

    # run synchronously in MVP; replace with Celery task for async
    report = service.run()

    # persist report if project provided
    if req.project_id:
        project = db.query(models.Project).get(req.project_id)
        if project:
            rep = models.Report(project_id=project.id, status='completed', payload=str(report))
            db.add(rep)
            db.commit()
            db.refresh(rep)

    _reports[job_id] = report
    return {"job_id": job_id, "status": "completed", "report": report}


@router.get("/reports/{job_id}")
def get_report(job_id: str):
    rep = _reports.get(job_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Report not found")
    return rep
