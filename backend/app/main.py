from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from starlette.middleware.sessions import SessionMiddleware

from app.database import SessionLocal, engine
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.participant import Participant
from app.auth.google import oauth

app = FastAPI()

# ✅ Session Middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# 🔐 GOOGLE LOGIN
# =========================

@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = "http://localhost:8000/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            return {"error": "User info not received"}

        email = user_info.get("email")
        name = user_info.get("name")

        # ✅ Save session
        request.session["user"] = {
            "email": email,
            "name": name
        }

        # ✅ Save to DB if new
        existing_user = db.query(User).filter(User.email == email).first()

        if not existing_user:
            new_user = User(name=name, email=email, role="analyst")
            db.add(new_user)
            db.commit()

        return RedirectResponse(url="http://localhost:3001/dashboard")

    except Exception as e:
        print("🔥 ERROR in /auth/callback:", str(e))
        return {"error": str(e)}


# =========================
# 👤 CURRENT USER
# =========================

@app.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")

    if not user:
        return {"error": "Not logged in"}

    db_user = db.query(User).filter(User.email == user["email"]).first()

    return {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name
    }

# =========================
# 📺 SESSIONS
# =========================

@app.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(SessionModel).all()

    result = []
    for s in sessions:
        count = db.query(Participant).filter(
            Participant.session_id == s.id
        ).count()

        result.append({
            "id": s.id,
            "topic": s.topic,
            "host_name": s.host_name,
            "max_participants": s.max_participants,
            "slots_left": s.max_participants - count,
            "scheduled_time": s.scheduled_time
        })

    return result

# =========================
# 🙋 JOIN SESSION
# =========================

@app.post("/join")
def join_session(data: dict, db: Session = Depends(get_db)):
    user_id = data["user_id"]
    session_id = data["session_id"]

    # Check limit
    count = db.query(Participant).filter(
        Participant.session_id == session_id
    ).count()

    session = db.query(SessionModel).filter(
        SessionModel.id == session_id
    ).first()

    if count >= session.max_participants:
        return {"message": "Session is full"}

    # Prevent duplicate
    existing = db.query(Participant).filter(
        Participant.user_id == user_id,
        Participant.session_id == session_id
    ).first()

    if existing:
        return {"message": "Already joined"}

    participant = Participant(
        user_id=user_id,
        session_id=session_id
    )

    db.add(participant)
    db.commit()

    return {"message": "Joined successfully"}

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}