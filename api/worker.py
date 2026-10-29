"""Polling worker for static inventory jobs; never executes generated code."""
from __future__ import annotations
import os, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from api.app import Job, Report, SessionLocal, SourceFile
from cobol2py_agent import analyze_repository, render_markdown

def run_once() -> bool:
    with SessionLocal.begin() as db:
        job=db.scalar(select(Job).where(Job.status=="queued").order_by(Job.created_at).with_for_update(skip_locked=True).limit(1))
        if job is None: return False
        job.status="running"; job.started_at=datetime.now(timezone.utc)
        jid,pid=job.id,job.project_id
    try:
        with SessionLocal() as db:
            sources=db.scalars(select(SourceFile).where(SourceFile.project_id==pid)).all()
            if not sources: raise RuntimeError("Project has no source files")
            with tempfile.TemporaryDirectory(prefix="cobol2py-job-") as tmp:
                root=Path(tmp).resolve()
                for source in sources:
                    target=(root/source.path).resolve()
                    if root not in target.parents: raise RuntimeError("Unsafe path")
                    target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_text(source.content,encoding="utf-8")
                data=analyze_repository(root); markdown=render_markdown(data)
            db.add(Report(project_id=pid,job_id=jid,report_json=data,report_markdown=markdown))
            job=db.get(Job,jid); job.status="succeeded"; job.finished_at=datetime.now(timezone.utc)
            db.commit()
    except Exception as exc:
        with SessionLocal.begin() as db:
            job=db.get(Job,jid)
            if job:
                job.status="failed"; job.error=f"{type(exc).__name__}: {str(exc)[:1500]}"
                job.finished_at=datetime.now(timezone.utc)
    return True

def main():
    delay=max(.25,float(os.getenv("COBOL2PY_WORKER_POLL_SECONDS","1")))
    while True:
        try: worked=run_once()
        except Exception: worked=False
        if not worked: time.sleep(delay)
if __name__=="__main__": main()
