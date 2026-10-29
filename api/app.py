"""Optional REST API backed by PostgreSQL.

The API stores source text and durable job state; a separate worker performs analysis.
It never executes translated Python or COBOL.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import DateTime, ForeignKey, String, Text, create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.types import JSON

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://cobol2py:cobol2py@localhost:5432/cobol2py")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
JSONType = JSON().with_variant(JSONB, "postgresql")


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SourceFile(Base):
    __tablename__ = "source_files"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(40), default="inventory")
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), unique=True)
    report_json: Mapped[dict[str, Any]] = mapped_column(JSONType)
    report_markdown: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


app = FastAPI(title="cobol2py API", version="0.1.0", description="REST API for static COBOL estate inventory and migration planning.")


@app.on_event("startup")
def create_schema() -> None:
    # Convenient bootstrap for the first iteration. Set false when a managed migration
    # workflow is in place; see docs/api.md before production deployment.
    if os.getenv("COBOL2PY_API_AUTO_CREATE_SCHEMA", "true").lower() == "true":
        Base.metadata.create_all(engine)


class Principal(BaseModel):
    subject: str


def current_principal(authorization: str | None = Header(default=None)) -> Principal:
    issuer = os.getenv("OIDC_ISSUER")
    audience = os.getenv("OIDC_AUDIENCE")
    if not issuer or not audience:
        if os.getenv("COBOL2PY_API_ALLOW_ANONYMOUS", "false").lower() == "true":
            return Principal(subject="local-development")
        raise HTTPException(status_code=503, detail="OIDC is not configured; set OIDC_ISSUER and OIDC_AUDIENCE")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required", headers={"WWW-Authenticate": "Bearer"})
    token = authorization[7:].strip()
    try:
        jwks_url = os.getenv("OIDC_JWKS_URL", issuer.rstrip("/") + "/.well-known/jwks.json")
        jwks = jwt.PyJWKClient(jwks_url)
        signing_key = jwks.get_signing_key_from_jwt(token).key
        claims = jwt.decode(token, signing_key, algorithms=["RS256", "ES256"], audience=audience, issuer=issuer)
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise jwt.InvalidTokenError("missing subject")
        return Principal(subject=subject)
    except (jwt.PyJWTError, ValueError, OSError) as exc:
        raise HTTPException(status_code=401, detail="Invalid bearer token", headers={"WWW-Authenticate": "Bearer"}) from exc


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class SourceCreate(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    content: str = Field(max_length=2_000_000)

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        path = PurePosixPath(normalized)
        if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
            raise ValueError("path must be a safe relative path without '..'")
        if re.match(r"^[A-Za-z]:", normalized):
            raise ValueError("drive-qualified paths are not allowed")
        if len(normalized) > 500:
            raise ValueError("path is too long")
        return normalized


def owned_project(session, project_id: str, principal: Principal) -> Project:
    project = session.get(Project, project_id)
    if project is None or project.owner_id != principal.subject:
        # Do not reveal whether another user's project exists.
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready"}


@app.post("/api/v1/projects", status_code=status.HTTP_201_CREATED, tags=["projects"])
def create_project(payload: ProjectCreate, principal: Principal = Depends(current_principal)) -> dict[str, Any]:
    with SessionLocal() as session:
        project = Project(name=payload.name.strip(), owner_id=principal.subject)
        session.add(project)
        session.commit()
        session.refresh(project)
        return {"id": project.id, "name": project.name, "created_at": project.created_at.isoformat()}


@app.get("/api/v1/projects", tags=["projects"])
def list_projects(principal: Principal = Depends(current_principal)) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        projects = session.scalars(select(Project).where(Project.owner_id == principal.subject).order_by(Project.created_at.desc())).all()
        return [{"id": p.id, "name": p.name, "created_at": p.created_at.isoformat()} for p in projects]


@app.post("/api/v1/projects/{project_id}/sources", status_code=status.HTTP_201_CREATED, tags=["sources"])
def add_source(project_id: str, payload: SourceCreate, principal: Principal = Depends(current_principal)) -> dict[str, Any]:
    with SessionLocal() as session:
        owned_project(session, project_id, principal)
        existing = session.scalar(select(SourceFile).where(SourceFile.project_id == project_id, SourceFile.path == payload.path))
        if existing:
            existing.content = payload.content
            session.commit()
            return {"id": existing.id, "path": existing.path, "updated": True}
        source = SourceFile(project_id=project_id, path=payload.path, content=payload.content)
        session.add(source)
        session.commit()
        session.refresh(source)
        return {"id": source.id, "path": source.path, "updated": False}


@app.get("/api/v1/projects/{project_id}/sources", tags=["sources"])
def list_sources(project_id: str, principal: Principal = Depends(current_principal)) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        owned_project(session, project_id, principal)
        rows = session.scalars(select(SourceFile).where(SourceFile.project_id == project_id).order_by(SourceFile.path)).all()
        return [{"id": row.id, "path": row.path, "characters": len(row.content)} for row in rows]


@app.post("/api/v1/projects/{project_id}/analyses", status_code=status.HTTP_202_ACCEPTED, tags=["jobs"])
def queue_analysis(project_id: str, principal: Principal = Depends(current_principal)) -> dict[str, Any]:
    with SessionLocal() as session:
        owned_project(session, project_id, principal)
        if not session.scalar(select(SourceFile.id).where(SourceFile.project_id == project_id).limit(1)):
            raise HTTPException(status_code=409, detail="Upload at least one source file before requesting analysis")
        job = Job(project_id=project_id, kind="inventory", status="queued")
        session.add(job)
        session.commit()
        session.refresh(job)
        return {"id": job.id, "project_id": project_id, "status": job.status, "status_url": f"/api/v1/jobs/{job.id}"}


@app.get("/api/v1/jobs/{job_id}", tags=["jobs"])
def get_job(job_id: str, principal: Principal = Depends(current_principal)) -> dict[str, Any]:
    with SessionLocal() as session:
        job = session.get(Job, job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        owned_project(session, job.project_id, principal)
        report = session.scalar(select(Report).where(Report.job_id == job.id))
        return {
            "id": job.id, "project_id": job.project_id, "kind": job.kind, "status": job.status,
            "error": job.error, "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "report_id": report.id if report else None,
        }


@app.get("/api/v1/projects/{project_id}/reports", tags=["reports"])
def list_reports(project_id: str, principal: Principal = Depends(current_principal)) -> list[dict[str, Any]]:
    with SessionLocal() as session:
        owned_project(session, project_id, principal)
        rows = session.scalars(select(Report).where(Report.project_id == project_id).order_by(Report.created_at.desc())).all()
        return [{"id": row.id, "job_id": row.job_id, "created_at": row.created_at.isoformat()} for row in rows]


@app.get("/api/v1/reports/{report_id}", tags=["reports"])
def get_report(report_id: str, principal: Principal = Depends(current_principal)) -> dict[str, Any]:
    with SessionLocal() as session:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        owned_project(session, report.project_id, principal)
        return {"id": report.id, "project_id": report.project_id, "job_id": report.job_id,
                "created_at": report.created_at.isoformat(), "data": report.report_json, "markdown": report.report_markdown}
