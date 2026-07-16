from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import io
import jwt

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import create_tables, get_db, User, ScanHistory
from model_util import predict_msg, find_spam_words, highlight_words, advanced_url_analysis

app = FastAPI(title="Spam Shield")
templates = Jinja2Templates(directory="templates")

SECRET_KEY  = "spamshield-uni-secret-2025-changeme"
ALGORITHM   = "HS256"
TOKEN_HOURS = 24
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

create_tables()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: int, username: str) -> str:
    payload = {
        "user_id":  user_id,
        "username": username,
        "exp":      datetime.utcnow() + timedelta(hours=TOKEN_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

def optional_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return decode_token(authorization.split(" ")[1])

def save_scan(db, user_payload, scan_type, input_content, result, confidence=None):
    if not user_payload:
        return
    try:
        scan = ScanHistory(
            user_id=user_payload["user_id"],
            scan_type=scan_type,
            input_content=input_content[:600],
            result=result,
            confidence=confidence
        )
        db.add(scan)
        db.commit()
    except Exception:
        db.rollback()

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class MessageRequest(BaseModel):
    text: str

class UrlRequest(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/auth/register")
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if not req.username.strip() or not req.email.strip() or not req.password:
        raise HTTPException(status_code=400, detail="All fields are required")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if db.query(User).filter(User.email == req.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(
        username=req.username.strip(),
        email=req.email.lower().strip(),
        hashed_password=hash_password(req.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.username)
    return {"token": token, "username": user.username}

@app.post("/api/auth/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower()).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user.id, user.username)
    return {"token": token, "username": user.username}

@app.post("/api/analyze")
async def analyze_message(
    req: MessageRequest,
    user: Optional[dict] = Depends(optional_user),
    db: Session = Depends(get_db)
):
    text = req.text.strip()
    if not text:
        return JSONResponse({"error": "No text provided"}, status_code=400)
    result, prob = predict_msg(text)
    confidence   = round(prob * 100, 2)
    suspicious   = find_spam_words(text)
    highlighted  = highlight_words(text, suspicious)
    save_scan(db, user, "message", text, result, confidence)
    return {"result": result, "confidence": confidence,
            "suspicious_words": suspicious, "highlighted_text": highlighted}

@app.post("/api/url")
async def check_url(
    req: UrlRequest,
    user: Optional[dict] = Depends(optional_user),
    db: Session = Depends(get_db)
):
    url = req.url.strip()
    if not url:
        return JSONResponse({"error": "No URL provided"}, status_code=400)
    result = advanced_url_analysis(url)
    save_scan(db, user, "url", url, result["status"], float(result["risk_score"]))
    return result

@app.post("/api/analyze-file")
async def analyze_file(
    file: UploadFile = File(...),
    user: Optional[dict] = Depends(optional_user),
    db: Session = Depends(get_db)
):
    content  = await file.read()
    messages = []
    if file.filename.endswith(".txt"):
        messages = [m for m in content.decode("utf-8").split("\n") if m.strip()]
    elif file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(content))
        messages = df.iloc[:, 0].dropna().tolist()
    else:
        return JSONResponse({"error": "Only .txt or .csv files are supported"}, status_code=400)
    results = []
    for msg in messages:
        pred, prob = predict_msg(str(msg))
        results.append({"message": str(msg)[:80], "prediction": pred,
                        "spam_probability": round(prob * 100, 2)})
    spam_count = sum(1 for r in results if r["prediction"] == "spam")
    save_scan(db, user, "batch", file.filename, f"{spam_count}/{len(results)} spam", None)
    return {"results": results, "total": len(results),
            "spam_count": spam_count, "ham_count": len(results) - spam_count}

@app.get("/api/history")
async def get_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scans = (db.query(ScanHistory)
             .filter(ScanHistory.user_id == current_user["user_id"])
             .order_by(ScanHistory.created_at.desc())
             .limit(200).all())
    return [{"id": s.id, "scan_type": s.scan_type, "input_content": s.input_content,
             "result": s.result, "confidence": s.confidence,
             "created_at": s.created_at.strftime("%d %b %Y, %H:%M")} for s in scans]

@app.delete("/api/history/{scan_id}")
async def delete_entry(
    scan_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scan = db.query(ScanHistory).filter(
        ScanHistory.id == scan_id,
        ScanHistory.user_id == current_user["user_id"]
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(scan)
    db.commit()
    return {"deleted": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
