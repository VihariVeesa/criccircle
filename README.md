# CricCircle

CricCircle is a professional cricket discussion platform where moderators and
analysts can host structured, time-bound sessions, build reputation through
ratings, and keep discussions professional.

## MVP Scope

- Google sign-in
- Role-based onboarding for `moderator` and `analyst`
- Session lobby with scheduled, live, and completed rooms
- Moderator-led room creation and participant management
- Join and leave flow with participant limits
- Post-session ratings

## Tech Stack

- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL
- Infra: Docker Compose and Nginx

## Environment Variables

Create `backend/.env` and add:

```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=supersecretkey
DATABASE_URL=postgresql://postgres:postgres@db:5432/criccircle
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## Access Modes

### Option A: Docker + Nginx

Use this when you want the full stack behind one main URL.

Update `backend/.env`:

```env
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost
```

Run:

```bash
docker-compose up --build
```

Open:

- App: [http://localhost](http://localhost)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Option B: Local frontend + local backend

Use this when you want React and FastAPI running separately.

Update `backend/.env`:

```env
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

Run the backend and frontend separately, then open:

- App: [http://localhost:3000](http://localhost:3000)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Google Login Setup

In Google Cloud Console, add these authorized redirect URIs:

- `http://localhost:8000/auth/callback`

Use this same callback for both the Docker + Nginx setup and the local split setup.

## Project Structure

```text
criccircle/
|-- backend/
|-- frontend/
|-- nginx/
|-- docker-compose.yml
`-- README.md
```

## Current Product Flow

1. Sign in with Google
2. Choose a role: moderator or analyst
3. Accept professional conduct rules
4. Enter the lobby
5. Moderators create rooms
6. Analysts join rooms
7. Rate participants after the session ends

## Notes

- Meeting links are hidden until a user joins the room.
- Ratings unlock only after a session is completed.
- Aadhaar authentication is not part of the current MVP implementation.
