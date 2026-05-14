import os
from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import httpx
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session, joinedload
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine, get_db
from app.models import Participant, Rating, Session as DebateSession, User
from app.schemas.participant import RemovalRequest
from app.schemas.rating import SessionRatingCreate
from app.schemas.session import SessionCreate
from app.schemas.user import OnboardingUpdate

load_dotenv()

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ALLOWED_ROLES = {"moderator", "analyst"}
MEET_CREATE_SCOPE = "https://www.googleapis.com/auth/meetings.space.created"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_MEET_SPACES_URL = "https://meet.googleapis.com/v2/spaces"

app = FastAPI(title="CricCircle API")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "development-secret"),
    same_site="lax",
    https_only=False,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth = OAuth()
oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": f"openid email profile {MEET_CREATE_SCOPE}"},
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_user_table_columns()


def utc_now():
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def to_naive_utc(value: datetime | None):
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def session_status(session: DebateSession):
    if session.status == "cancelled":
        return "cancelled"

    start = normalize_datetime(session.scheduled_time)
    end = start + timedelta_minutes(session.duration_minutes)
    now = utc_now()

    if now < start:
        return "scheduled"
    if now <= end:
        return "live"
    return "completed"


def timedelta_minutes(minutes: int):
    from datetime import timedelta

    return timedelta(minutes=minutes)


def active_participants(session: DebateSession):
    return [participant for participant in session.participants if participant.is_active]


def user_is_joined(session: DebateSession, user_id: int):
    return any(participant.user_id == user_id for participant in active_participants(session))


def serialize_user(user: User):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "bio": user.bio,
        "averageRating": round(user.average_rating or 0, 2),
        "ratingsCount": user.ratings_count or 0,
        "rulesAccepted": bool(user.rules_accepted_at),
        "onboardingComplete": bool(user.role and user.rules_accepted_at),
    }


def ensure_user_table_columns():
    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("users")}
    additions = {
        "google_access_token": "TEXT",
        "google_refresh_token": "TEXT",
        "google_token_scope": "TEXT",
        "google_token_expires_at": "TIMESTAMP",
    }

    with engine.begin() as connection:
        for column_name, column_type in additions.items():
            if column_name not in columns:
                connection.execute(
                    text(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
                )


def token_has_meet_scope(user: User):
    scopes = (user.google_token_scope or "").split()
    return MEET_CREATE_SCOPE in scopes


def token_is_usable(user: User):
    expires_at = to_naive_utc(user.google_token_expires_at)
    if not user.google_access_token:
        return False
    if not expires_at:
        return True
    return expires_at > (utc_now() - timedelta_minutes(5)).replace(tzinfo=None)


def store_google_token(user: User, token: dict):
    user.google_access_token = token.get("access_token") or user.google_access_token
    user.google_refresh_token = token.get("refresh_token") or user.google_refresh_token
    user.google_token_scope = token.get("scope") or user.google_token_scope

    expires_at = token.get("expires_at")
    if expires_at:
        user.google_token_expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)
    elif token.get("expires_in"):
        user.google_token_expires_at = utc_now() + timedelta_minutes(
            max(int(token["expires_in"]) // 60, 1)
        )


def refresh_google_access_token(user: User):
    if token_is_usable(user):
        return user.google_access_token

    if not user.google_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please sign out and sign in again to grant Google Meet access.",
        )

    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "refresh_token": user.google_refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=20.0,
    )
    payload = response.json()
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=payload.get("error_description")
            or payload.get("error")
            or "Could not refresh Google access token.",
        )

    refreshed_token = {
        "access_token": payload.get("access_token"),
        "scope": payload.get("scope", user.google_token_scope),
    }
    if payload.get("expires_in"):
        refreshed_token["expires_at"] = int(utc_now().timestamp()) + int(payload["expires_in"])
    store_google_token(user, refreshed_token)
    return user.google_access_token


def create_google_meet_space(user: User, db: Session):
    if not token_has_meet_scope(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please sign out and sign in again so CricCircle can create Google Meet links automatically.",
        )

    access_token = refresh_google_access_token(user)
    response = httpx.post(
        GOOGLE_MEET_SPACES_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={},
        timeout=20.0,
    )
    payload = response.json()
    if response.status_code >= 400:
        message = payload.get("error", {}).get("message") if isinstance(payload.get("error"), dict) else None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message or "Google Meet space creation failed.",
        )

    db.add(user)
    db.commit()
    return payload


def serialize_session(session: DebateSession, viewer: User):
    status_value = session_status(session)
    participants = active_participants(session)
    joined = user_is_joined(session, viewer.id)
    is_host = session.host_id == viewer.id
    participant_payload = [
        {
            "id": participant.user.id,
            "name": participant.user.name,
            "role": participant.user.role,
            "averageRating": round(participant.user.average_rating or 0, 2),
            "ratingsCount": participant.user.ratings_count or 0,
            "joinedAt": participant.joined_at.isoformat(),
        }
        for participant in participants
    ]
    involved_users = {session.host_id: session.host}
    for participant in participants:
        involved_users[participant.user_id] = participant.user

    rating_targets = []
    if status_value == "completed" and viewer.id in involved_users:
        for target_id, target_user in involved_users.items():
            if target_id == viewer.id:
                continue
            existing_rating = next(
                (
                    rating
                    for rating in session.ratings
                    if rating.rater_user_id == viewer.id and rating.rated_user_id == target_id
                ),
                None,
            )
            rating_targets.append(
                {
                    "userId": target_user.id,
                    "name": target_user.name,
                    "role": target_user.role,
                    "existingScore": existing_rating.score if existing_rating else None,
                    "existingFeedback": existing_rating.feedback if existing_rating else "",
                }
            )

    return {
        "id": session.id,
        "topic": session.topic,
        "description": session.description,
        "scheduledTime": session.scheduled_time.isoformat(),
        "durationMinutes": session.duration_minutes,
        "maxParticipants": session.max_participants,
        "joinedCount": len(participants),
        "slotsLeft": max(session.max_participants - len(participants), 0),
        "status": status_value,
        "meetingLink": session.meeting_link if (joined or is_host) else None,
        "meetingLinkLocked": bool(session.meeting_link and not (joined or is_host)),
        "host": {
            "id": session.host.id,
            "name": session.host.name,
            "role": session.host.role,
            "averageRating": round(session.host.average_rating or 0, 2),
            "ratingsCount": session.host.ratings_count or 0,
        },
        "participants": participant_payload,
        "joined": joined,
        "isHost": is_host,
        "canManage": is_host,
        "ratingTargets": rating_targets,
    }


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_onboarded_user(user: User = Depends(get_current_user)):
    if not user.role or not user.rules_accepted_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete onboarding before using the platform",
        )
    return user


def get_session_or_404(db: Session, session_id: int):
    session = (
        db.query(DebateSession)
        .options(
            joinedload(DebateSession.host),
            joinedload(DebateSession.participants).joinedload(Participant.user),
            joinedload(DebateSession.ratings),
        )
        .filter(DebateSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


def recalculate_user_rating(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    ratings = db.query(Rating).filter(Rating.rated_user_id == user_id).all()
    if not user:
        return
    if not ratings:
        user.average_rating = 0
        user.ratings_count = 0
        return
    user.ratings_count = len(ratings)
    user.average_rating = sum(rating.score for rating in ratings) / len(ratings)


@app.get("/")
@app.get("/api/health")
def health():
    return {"message": "CricCircle API is running"}


@app.get("/login/google")
@app.get("/auth/google/login")
@app.get("/api/auth/google/login")
async def login_google(request: Request):
    redirect_uri = f"{BACKEND_URL}/auth/callback"
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )


@app.get("/auth/callback")
@app.get("/api/auth/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read Google profile",
        )

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name") or email

    user = None
    if google_sub:
        user = db.query(User).filter(User.google_sub == google_sub).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            name=name,
            email=email,
            google_sub=google_sub,
        )
        db.add(user)
    else:
        user.name = name
        user.email = email
        if google_sub and not user.google_sub:
            user.google_sub = google_sub

    store_google_token(user, token)

    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    return RedirectResponse(url=FRONTEND_URL)


@app.get("/me")
@app.get("/api/me")
def get_me(user: User = Depends(get_current_user)):
    return serialize_user(user)


@app.post("/onboarding")
@app.post("/api/onboarding")
def complete_onboarding(
    payload: OnboardingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    role = payload.role.strip().lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role")
    if not payload.rules_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the professional conduct rules",
        )

    user.role = role
    user.bio = payload.bio.strip() if payload.bio else None
    user.rules_accepted_at = utc_now()
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@app.post("/logout")
@app.post("/auth/logout")
@app.post("/api/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"success": True}


@app.get("/logout")
def logout_redirect(request: Request):
    request.session.clear()
    return RedirectResponse(url=FRONTEND_URL)


@app.get("/sessions")
@app.get("/api/sessions")
def list_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(get_onboarded_user),
):
    sessions = (
        db.query(DebateSession)
        .options(
            joinedload(DebateSession.host),
            joinedload(DebateSession.participants).joinedload(Participant.user),
            joinedload(DebateSession.ratings),
        )
        .order_by(DebateSession.scheduled_time.asc())
        .all()
    )
    return [serialize_session(session, user) for session in sessions]


@app.post("/sessions")
@app.post("/api/sessions")
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_onboarded_user),
):
    if user.role != "moderator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only moderators can create sessions",
        )
    if payload.max_participants < 2 or payload.max_participants > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Participant limit must be between 2 and 12",
        )
    if payload.duration_minutes < 15 or payload.duration_minutes > 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be between 15 and 180 minutes",
        )

    session = DebateSession(
        topic=payload.topic.strip(),
        description=payload.description.strip() if payload.description else None,
        host_id=user.id,
        scheduled_time=normalize_datetime(payload.scheduled_time),
        duration_minutes=payload.duration_minutes,
        max_participants=payload.max_participants,
    )
    meet_space = create_google_meet_space(user, db)
    session.meeting_link = meet_space.get("meetingUri")
    db.add(session)
    db.commit()
    return serialize_session(get_session_or_404(db, session.id), user)


@app.post("/sessions/{session_id}/join")
@app.post("/api/sessions/{session_id}/join")
def join_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_onboarded_user),
):
    session = get_session_or_404(db, session_id)
    if session.host_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You are hosting this session")
    if session_status(session) == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This session has ended")

    existing = (
        db.query(Participant)
        .filter(Participant.session_id == session_id, Participant.user_id == user.id)
        .first()
    )
    if existing and existing.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already joined")

    if len(active_participants(session)) >= session.max_participants:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is full")

    if existing:
        existing.is_active = True
        existing.removed_at = None
        existing.removed_reason = None
        existing.joined_at = utc_now()
    else:
        db.add(Participant(user_id=user.id, session_id=session_id))

    db.commit()
    return serialize_session(get_session_or_404(db, session_id), user)


@app.post("/sessions/{session_id}/leave")
@app.post("/api/sessions/{session_id}/leave")
def leave_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_onboarded_user),
):
    participant = (
        db.query(Participant)
        .filter(
            Participant.session_id == session_id,
            Participant.user_id == user.id,
            Participant.is_active.is_(True),
        )
        .first()
    )
    if not participant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have not joined this session")

    participant.is_active = False
    participant.removed_at = utc_now()
    participant.removed_reason = "Left voluntarily"
    db.commit()
    return serialize_session(get_session_or_404(db, session_id), user)


@app.post("/sessions/{session_id}/remove/{participant_user_id}")
@app.post("/api/sessions/{session_id}/remove/{participant_user_id}")
def remove_participant(
    session_id: int,
    participant_user_id: int,
    payload: RemovalRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_onboarded_user),
):
    session = get_session_or_404(db, session_id)
    if session.host_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the moderator hosting the session can remove participants",
        )

    participant = (
        db.query(Participant)
        .filter(
            Participant.session_id == session_id,
            Participant.user_id == participant_user_id,
            Participant.is_active.is_(True),
        )
        .first()
    )
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    participant.is_active = False
    participant.removed_at = utc_now()
    participant.removed_reason = payload.reason or "Removed by moderator"
    db.commit()
    return serialize_session(get_session_or_404(db, session_id), user)


@app.post("/sessions/{session_id}/ratings")
@app.post("/api/sessions/{session_id}/ratings")
def rate_session_participant(
    session_id: int,
    payload: SessionRatingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_onboarded_user),
):
    session = get_session_or_404(db, session_id)
    if session_status(session) != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ratings open after the session ends")
    if payload.rated_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot rate yourself")

    involved_ids = {session.host_id}
    involved_ids.update(participant.user_id for participant in active_participants(session))
    if user.id not in involved_ids or payload.rated_user_id not in involved_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only session participants can rate each other",
        )

    rating = (
        db.query(Rating)
        .filter(
            Rating.session_id == session_id,
            Rating.rater_user_id == user.id,
            Rating.rated_user_id == payload.rated_user_id,
        )
        .first()
    )

    if rating:
        rating.score = payload.score
        rating.feedback = payload.feedback.strip() if payload.feedback else None
    else:
        db.add(
            Rating(
                session_id=session_id,
                rater_user_id=user.id,
                rated_user_id=payload.rated_user_id,
                score=payload.score,
                feedback=payload.feedback.strip() if payload.feedback else None,
            )
        )

    db.commit()
    recalculate_user_rating(db, payload.rated_user_id)
    db.commit()
    return serialize_session(get_session_or_404(db, session_id), user)
