import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app import main
from app.database import Base, SessionLocal, get_db


class PanelJourneyTest(unittest.TestCase):
    def test_moderator_hosts_and_analyst_joins_then_leaves(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(
                f"sqlite:///{Path(directory, 'test.db').as_posix()}",
                connect_args={"check_same_thread": False},
            )
            try:
                Base.metadata.create_all(engine)

                def test_db():
                    with SessionLocal(bind=engine) as db:
                        yield db

                with patch.dict(main.app.dependency_overrides, {get_db: test_db}):
                    self.check_panel()
            finally:
                engine.dispose()

    def sign_in(self, client, role):
        token = {
            "access_token": f"test-{role}",
            "scope": main.MEET_CREATE_SCOPE,
            "userinfo": {"sub": role, "email": f"{role}@example.org", "name": role},
        }
        with patch.object(main.oauth.google, "authorize_access_token", AsyncMock(return_value=token)):
            response = client.get("/auth/callback", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        response = client.post("/api/onboarding", json={"role": role, "rules_accepted": True})
        self.assertEqual(response.status_code, 200, response.text)

    def check_panel(self):
        # No lifespan startup: all route dependencies use the isolated test database.
        moderator, analyst = TestClient(main.app), TestClient(main.app)
        self.addCleanup(moderator.close)
        self.addCleanup(analyst.close)
        self.sign_in(moderator, "moderator")
        self.sign_in(analyst, "analyst")
        payload = {
            "topic": "Death-over bowling",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
            "max_participants": 4,
        }
        self.assertEqual(analyst.post("/api/sessions", json=payload).status_code, 403)
        link = "https://meet.example.org/test-room"
        with patch.object(main.httpx, "post", return_value=httpx.Response(200, json={"meetingUri": link})) as create:
            created = moderator.post("/api/sessions", json=payload)
        self.assertEqual(created.status_code, 200, created.text)
        self.assertEqual(create.call_args.args, (main.GOOGLE_MEET_SPACES_URL,))
        self.assertEqual(create.call_args.kwargs["headers"]["Authorization"], "Bearer test-moderator")
        self.assertEqual(created.json()["meetingLink"], link)
        panel = analyst.get("/api/sessions").json()[0]
        self.assertEqual(panel["status"], "live")
        self.assertEqual(panel["slotsLeft"], 4)
        self.assertIsNone(panel["meetingLink"])
        path = f"/api/sessions/{panel['id']}"
        joined = analyst.post(path + "/join")
        self.assertEqual(joined.status_code, 200, joined.text)
        self.assertEqual(joined.json()["meetingLink"], link)
        self.assertEqual(moderator.get("/api/sessions").json()[0]["slotsLeft"], 3)
        left = analyst.post(path + "/leave")
        self.assertEqual(left.status_code, 200, left.text)
        self.assertEqual(left.json()["slotsLeft"], 4)
        self.assertIsNone(analyst.get("/api/sessions").json()[0]["meetingLink"])
