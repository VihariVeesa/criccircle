import React, { useEffect, useState } from "react";

function Dashboard() {
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);

  // 🔁 Fetch logged-in user
  useEffect(() => {
    fetch("/api/me", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.error) {
          setUser(data);
        }
      })
      .catch((err) => console.error("User fetch error:", err));
  }, []);

  // 🔁 Fetch sessions
  useEffect(() => {
    fetch("/api/sessions", {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => setSessions(data))
      .catch((err) => console.error("Sessions fetch error:", err));
  }, []);

  // 🔥 Helper: calculate slots left
  const getSlotsLeft = (session) => {
    return session.maxParticipants - session.joined;
  };

  // 🔥 Helper: calculate time left
  const getTimeLeft = (session) => {
    const start = new Date(session.startTime);
    const now = new Date();

    const end = new Date(start.getTime() + session.duration * 60000);

    const diff = end - now;

    if (diff <= 0) return "Ended";

    const mins = Math.floor(diff / 60000);
    return `${mins} mins left`;
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>🏏 CricCircle</h1>

      <h2>🔥 Live Debate Sessions</h2>

      <h3>
        Welcome, {user ? user.name : "Loading..."}
      </h3>

      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
        {sessions.map((session) => (
          <div
            key={session.id}
            style={{
              border: "1px solid #ddd",
              borderRadius: "10px",
              padding: "20px",
              width: "300px",
              background: "#f9f9f9",
            }}
          >
            <h3>{session.title}</h3>

            <p>👤 Host: {session.host}</p>

            <p>👥 Slots Left: {getSlotsLeft(session)}</p>

            <p>⏳ {getTimeLeft(session)}</p>

            <button
              style={{
                marginTop: "10px",
                padding: "10px",
                backgroundColor: "#007bff",
                color: "white",
                border: "none",
                borderRadius: "5px",
                cursor: "pointer",
              }}
            >
              Join Now 🚀
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Dashboard;