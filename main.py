# main.py
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

# Basic auth config
security = HTTPBasic()
USERS = {"attorney": "password123"}
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# DB setup
_db = DB()
_db.init_db()

# Auth helper
def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = USERS.get(credentials.username)
    if not correct_password or not secrets.compare_digest(credentials.password, correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.username

@app.post("/lead")
def create_lead(
        first_name: str = Form(...),
        last_name: str = Form(...),
        email: EmailStr = Form(...),
        resume: UploadFile = File(...)
):
    file_location = os.path.join(UPLOAD_DIR, resume.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)

    with sqlite3.connect(_db.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO leads (first_name, last_name, email, resume) VALUES (?, ?, ?, ?)''',
            (first_name, last_name, email, file_location)
        )
        conn.commit()

    print(f"Email sent to {email} and attorney@company.com")
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
