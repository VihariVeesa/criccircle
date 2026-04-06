from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import engine, Base, SessionLocal

from fastapi import Request
from app.auth.google import oauth
from starlette.middleware.sessions import SessionMiddleware

# Import models (VERY IMPORTANT for table creation)
from app.models import user, session, participant
from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.participant import Participant

# Import schemas
from app.schemas.user import UserCreate
from app.schemas.session import SessionCreate
from app.schemas.participant import JoinSession

# Create app FIRST
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Create tables
Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------ BASIC ROUTES ------------------

@app.get("/")
def home():
    return {"message": "CricCircle Backend Running 🚀"}


@app.get("/health")
def health_check():
    return {"status": "OK"}


# ------------------ USER APIs ------------------

@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        name=user.name,
        email=user.email,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


# ------------------ SESSION APIs ------------------

@app.post("/sessions")
def create_session(session: SessionCreate, db: Session = Depends(get_db)):
    new_session = SessionModel(
        topic=session.topic,
        host_name=session.host_name,
        scheduled_time=session.scheduled_time,
        max_participants=session.max_participants
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session


@app.get("/sessions")
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(SessionModel).all()
    return sessions


# ------------------ JOIN SESSION ------------------

@app.post("/join")
def join_session(data: JoinSession, db: Session = Depends(get_db)):
    
    # Check duplicate join
    existing = db.query(Participant).filter(
        Participant.user_id == data.user_id,
        Participant.session_id == data.session_id
    ).first()

    if existing:
        return {"message": "User already joined this session"}

    # Get session details
    session = db.query(SessionModel).filter(
        SessionModel.id == data.session_id
    ).first()

    if not session:
        return {"message": "Session not found"}

    # Count participants
    count = db.query(Participant).filter(
        Participant.session_id == data.session_id
    ).count()

    if count >= session.max_participants:
        return {"message": "Session is full"}

    participant = Participant(
        user_id=data.user_id,
        session_id=data.session_id
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return participant

@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = "http://127.0.0.1:8000/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    
    user_info = token.get("userinfo")
    
    return {
        "message": "Login successful",
        "user": user_info
    }

