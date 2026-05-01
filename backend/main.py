from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid

import scraper
import worker

app = FastAPI(title="Form Automator API")

# Allow all origins for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UrlPayload(BaseModel):
    url: str

class JobPayload(BaseModel):
    action: str
    hidden_fields: Dict[str, str]
    fields: List[Dict[str, Any]]
    count: int

@app.post("/api/parse")
def parse_endpoint(payload: UrlPayload):
    result = scraper.scrape_form(payload.url)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/start")
def start_endpoint(payload: JobPayload, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    background_tasks.add_task(worker.start_job, job_id, payload.dict())
    return {"job_id": job_id}

@app.get("/api/progress/{job_id}")
def progress_endpoint(job_id: str):
    state = worker.get_job_state(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found")
    return state
