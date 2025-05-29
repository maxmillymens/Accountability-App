# 📌 Project: AI Accountability Buddy App

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import sqlite3

app = FastAPI()

# Allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Database Setup ----------
conn = sqlite3.connect("accountability.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    tone TEXT DEFAULT 'coach'
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS struggles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    start_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    struggle_id INTEGER,
    date TEXT,
    status TEXT,
    comment TEXT,
    FOREIGN KEY(struggle_id) REFERENCES struggles(id)
)
''')

conn.commit()

# ---------- Models ----------
class User(BaseModel):
    username: str
    tone: Optional[str] = "coach"

class Struggle(BaseModel):
    username: str
    struggle: str

class LogEntry(BaseModel):
    struggle_id: int
    status: str  # 'success', 'fail', 'struggled'
    comment: Optional[str] = ""

# ---------- Routes ----------
@app.post("/register")
def register_user(user: User):
    try:
        c.execute("INSERT INTO users (username, tone) VALUES (?, ?)", (user.username, user.tone))
        conn.commit()
        return {"message": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/add_struggle")
def add_struggle(data: Struggle):
    c.execute("SELECT id FROM users WHERE username=?", (data.username,))
    user = c.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_id = user[0]
    c.execute("INSERT INTO struggles (user_id, name, start_date) VALUES (?, ?, ?)",
              (user_id, data.struggle, datetime.utcnow().isoformat()))
    conn.commit()
    return {"message": "Struggle added"}

@app.post("/log")
def log_entry(entry: LogEntry):
    c.execute("INSERT INTO logs (struggle_id, date, status, comment) VALUES (?, ?, ?, ?)",
              (entry.struggle_id, datetime.utcnow().date().isoformat(), entry.status, entry.comment))
    conn.commit()
    return {"message": "Log recorded"}

@app.get("/streak/{struggle_id}")
def get_streak(struggle_id: int):
    c.execute("SELECT date, status FROM logs WHERE struggle_id=? ORDER BY date DESC", (struggle_id,))
    logs = c.fetchall()
    streak = 0
    for log in logs:
        if log[1] == "success":
            streak += 1
        else:
            break
    return {"current_streak": streak, "log_count": len(logs)}
@app.get("/get_struggles")
def get_user_struggles(username: str):
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user = c.fetchone()
    if not user:
        return {"struggles": {}}
    user_id = user[0]
    c.execute("SELECT id, name FROM struggles WHERE user_id=?", (user_id,))
    results = c.fetchall()
    return {"struggles": {name: struggle_id for struggle_id, name in results}}

@app.get("/logs/{struggle_id}")
def get_all_logs(struggle_id: int):
    c.execute("SELECT date, status FROM logs WHERE struggle_id=?", (struggle_id,))
    return {"logs": c.fetchall()}

