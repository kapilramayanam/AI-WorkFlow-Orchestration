# Project: AI Workflow Orchestration Platform

# --- Backend (FastAPI) ---
# File: main.py

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import List
import uuid
import subprocess
import os

app = FastAPI()

# Simulate job storage
jobs = {}

class JobRequest(BaseModel):
    name: str
    command: str  # Shell command to run training

class JobStatus(BaseModel):
    job_id: str
    name: str
    status: str
    logs: List[str] = []

# Background task to run training job
def run_training_job(job_id: str, command: str):
    jobs[job_id]["status"] = "running"
    log_file = f"logs/{job_id}.log"
    with open(log_file, "w") as f:
        process = subprocess.Popen(command, shell=True, stdout=f, stderr=subprocess.STDOUT)
        process.wait()
    jobs[job_id]["status"] = "completed" if process.returncode == 0 else "failed"

@app.post("/start-job")
def start_job(job: JobRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"name": job.name, "status": "queued"}
    background_tasks.add_task(run_training_job, job_id, job.command)
    return {"job_id": job_id, "status": "queued"}

@app.get("/job-status/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return {"error": "Job not found"}
    log_file = f"logs/{job_id}.log"
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            logs = f.readlines()
    return JobStatus(job_id=job_id, name=job["name"], status=job["status"], logs=logs)
