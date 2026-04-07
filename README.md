# 🏏 CricCircle

CricCircle is a professional cricket discussion platform where users can join moderated sessions, share insights, and engage in structured conversations.

The goal is to create a **LinkedIn-style environment for cricket analysts**, ensuring discussions are meaningful, respectful, and structured.

---

# 🚀 Tech Stack

## Backend

* FastAPI (Python)
* PostgreSQL
* SQLAlchemy
* Google OAuth (Authentication)

## Frontend

* React.js
* Axios

## DevOps / Infrastructure

* Docker
* Docker Compose
* Nginx

---

# 📦 Features (MVP)

* Google Login Authentication
* Session Creation & Listing
* Join Session with slot limits
* Participant Tracking
* Time-based session handling
* Professional discussion environment

---

# 🧱 Architecture

Frontend (React) → Nginx → Backend (FastAPI) → PostgreSQL

---

# ⚙️ Prerequisites

Make sure the following are installed:

* Docker Desktop
* Git
* (Optional) Node.js (only if running frontend separately)

---

# 📁 Project Structure

criccircle/
│
├── backend/
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
│
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md

---

# 🔐 Environment Variables

Create a file:

backend/.env

Add the following:

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
SECRET_KEY=supersecretkey
DATABASE_URL=postgresql://postgres:postgres@db:5432/criccircle

---

# 🐳 How to Run the Project

## Step 1: Clone Repository

git clone https://github.com/YOUR_USERNAME/criccircle.git
cd criccircle

---

## Step 2: Start the Application

docker-compose up --build

---

## ✅ That’s it. The platform will start automatically.

---

# 🌐 Access the Application

Frontend: http://localhost
Backend API: http://localhost:8000
Swagger Docs: http://localhost:8000/docs

---

# 🔑 Google Login Setup

1. Go to Google Cloud Console
2. Create OAuth Client ID
3. Choose: Web Application

Add this Authorized Redirect URI:

http://localhost:8000/auth/callback

4. Copy Client ID & Secret into `.env`

---

# 🧪 How to Use

1. Open: http://localhost
2. Click **Login with Google**
3. After login, dashboard will load
4. View available sessions
5. Join sessions (limited slots)
6. Participate in discussions

---

# 📊 Core Functionalities

## Session System

* Each session has a fixed participant limit
* Prevents overcrowding
* Ensures structured discussions

## Authentication

* Google OAuth ensures real users
* Session-based login handling

## Professional Environment

* Designed for meaningful cricket analysis
* Avoids spam and unstructured chats

---

# 🔁 Stop / Restart Application

Stop:
docker-compose down

Restart:
docker-compose up

---

# 🧹 Clean Reset (if something breaks)

docker-compose down -v
docker system prune -a -f
docker-compose up --build

---

# ⚠️ Common Issues & Fixes

## Port already in use

Change ports in docker-compose.yml

---

## Google Login not working

* Verify redirect URI
* Check Client ID & Secret

---

## Backend not starting

Check logs:
docker-compose logs backend

---

## Database issues

Ensure DATABASE_URL uses:
db (NOT localhost)

---

# 🚀 Future Enhancements

* Live video discussions (WebRTC)
* Session recording & playback
* AI moderation for toxicity
* Leaderboard for analysts
* Monetization (subscriptions)

---

# 👨‍💻 Author

Sunny Vihari Veesa
Senior Program Manager | DevOps | Product Builder

---

# 💡 Vision

CricCircle aims to become a platform where:

* Cricket discussions are professional
* Analysts build credibility
* Conversations create real value

A structured alternative to noisy social media.

---

# ⭐ Final Note

This project is fully dockerized.

Anyone can run it using:

docker-compose up --build

No manual setup required.

---