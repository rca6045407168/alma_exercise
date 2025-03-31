# main.py (Refactored)

from fastapi import FastAPI, HTTPException, Depends, Form, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import EmailStr
from typing import List
import shutil
import secrets
import os
import sqlite3
import mimetypes
import logging

from db.sql_lite import DB
from model.lead_model import Lead

app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication config
security = HTTPBasic()
USERS = {"attorney": "password123"}  # NOTE: Replace with hashed passwords and env vars in production
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# DB setup
_db = DB()
_db.init_db()

# --- Helper functions ---
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = USERS.get(credentials.username)
    if not correct_password or not secrets.compare_digest(credentials.password, correct_password):
        logger.warning(f"Failed auth attempt for username: {credentials.username}")
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

def send_email_notification(email: str):
    # Simulate sending email, or replace with actual email service like SendGrid
    logger.info(f"Email sent to {email} and attorney@company.com")

def is_valid_resume(file: UploadFile):
    allowed_types = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    return file.content_type in allowed_types

# --- API Endpoints ---
@app.post("/lead")
def create_lead(
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: EmailStr = Form(...),
        resume: UploadFile = File(...)
):
    if not is_valid_resume(resume):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF or Word documents allowed.")

    file_location = os.path.join(UPLOAD_DIR, resume.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    with sqlite3.connect(_db.DATABASE) as conn:
        cursor = conn.cursor()

        # Check for duplicate email
        existing = cursor.execute("SELECT * FROM leads WHERE email = ?", (email,)).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="A lead with this email already exists.")

        cursor.execute(
            '''INSERT INTO leads (first_name, last_name, email, resume) VALUES (?, ?, ?, ?)''',
            (first_name, last_name, email, file_location)
        )
        conn.commit()

    send_email_notification(email)
    return {"message": "Lead submitted successfully"}

@app.get("/leads", response_model=List[Lead])
def get_leads(username: str = Depends(get_current_username)):
    with sqlite3.connect(_db.DATABASE) as conn:
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM leads").fetchall()
        return [Lead(id=row[0], first_name=row[1], last_name=row[2], email=row[3], resume=row[4], state=row[5]) for row in rows]

@app.put("/lead/{lead_id}/reach_out")
def mark_as_reached_out(lead_id: int, username: str = Depends(get_current_username)):
    with sqlite3.connect(_db.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE leads SET state = 'REACHED_OUT' WHERE id = ?", (lead_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
        conn.commit()
    return {"message": "Lead marked as REACHED_OUT"}

@app.get("/")
def root():
    return {"message": "Backend Engineer Take Home Exercise API"}