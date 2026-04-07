from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from authlib.integrations.starlette_client import OAuth

import os
from dotenv import load_dotenv

# Load env
load_dotenv()

app = FastAPI()

# ENV VARIABLES
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY")

BACKEND_URL = os.getenv("BACKEND_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

# Session Middleware (FIXED)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False
)

# CORS (FIXED)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth Setup
oauth = OAuth()

oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# Root
@app.get("/")
def home():
    return {"message": "CricCircle Backend Running 🚀"}


# Login Route
@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = f"{BACKEND_URL}/auth/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


# Callback Route
@app.get("/auth/callback")
async def auth_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get("userinfo")

        # Save user in session
        request.session["user"] = {
            "email": user["email"],
            "name": user["name"]
        }

        return RedirectResponse("http://localhost/dashboard")

    except Exception as e:
        return JSONResponse({"error": str(e)})


# Get logged-in user
@app.get("/me")
def get_me(request: Request):
    user = request.session.get("user")

    if not user:
        return JSONResponse({"error": "Not logged in"}, status_code=401)

    return user


# Sample sessions (dummy data for UI)
@app.get("/sessions")
def get_sessions():
    return [
        {
            "id": 1,
            "title": "CSK vs MI - Who has better bowling?",
            "host": "Sunny",
            "maxParticipants": 5,
            "joined": 2,
            "duration": 60,  # minutes
            "startTime": "2026-04-07T10:00:00"
        },
        {
            "id": 2,
            "title": "RCB vs KKR - Best batting lineup?",
            "host": "Sunny",
            "maxParticipants": 5,
            "joined": 3,
            "duration": 60,
            "startTime": "2026-04-07T11:00:00"
        }
    ]