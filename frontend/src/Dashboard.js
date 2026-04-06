import { useEffect, useState } from "react";
import "./App.css";

function Dashboard() {
  const [sessions, setSessions] = useState([]);
  const [user, setUser] = useState(null);

  // ✅ Helper: Time left
  const getTimeLeft = (scheduledTime) => {
    const start = new Date(scheduledTime);
    const now = new Date();

    const end = new Date(start.getTime() + 60 * 60 * 1000); // +1 hour
    const diff = end - now;

    if (diff <= 0) return "Ended";

    const mins = Math.floor(diff / 60000);
    return `${mins} mins left`;
  };

  // Fetch sessions
  useEffect(() => {
    fetch("http://localhost:8000/sessions", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setSessions(data));
  }, []);

  // Fetch user
  useEffect(() => {
    fetch("http://localhost:8000/me", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setUser(data));
  }, []);

  // Join session
  const joinSession = async (sessionId) => {
    if (!user?.id) {
      alert("User not loaded yet");
      return;
    }

    const res = await fetch("http://localhost:8000/join", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: user.id,
        session_id: sessionId,
      }),
    });

    const data = await res.json();
    alert(data.message);
  };

  return (
    <div>
      {/* Navbar */}
      <div className="navbar">
        <h2>CricCircle 🏏</h2>
        <div className="nav-right">
          <span>{user?.name || "Loading..."}</span>
          <button
            className="logout-btn"
            onClick={() => {
              fetch("http://localhost:8000/logout", {
                credentials: "include",
              }).then(() => {
                window.location.href =
                  "http://localhost:8000/login/google";
              });
            }}
          >
            Logout
          </button>
        </div>
      </div>

      {/* Main */}
      <div className="dashboard">
        <h1>🔥 Live Debate Sessions</h1>

        <div className="session-list">
          {sessions.map((s) => (
            <div key={s.id} className="session-card">
              <h3>{s.topic}</h3>

              <p>👤 Host: {s.host_name}</p>
              <p>👥 Slots Left: {s.slots_left}</p>
              <p>⏳ {getTimeLeft(s.scheduled_time)}</p>

              {s.is_host ? (
                <button style={{ background: "green" }}>
                  Start Session 🎤
                </button>
              ) : (
                <button
                  disabled={!user || s.slots_left === 0}
                  onClick={() => joinSession(s.id)}
                >
                  {s.slots_left === 0 ? "Full ❌" : "Join Now 🚀"}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;