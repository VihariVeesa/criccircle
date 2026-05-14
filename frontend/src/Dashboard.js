import { useEffect, useMemo, useState } from "react";

const defaultSessionForm = {
  topic: "",
  description: "",
  scheduledTime: "",
  durationMinutes: 60,
  maxParticipants: 4,
};

function Dashboard({ onLogout, onUserRefresh, user }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [sessionForm, setSessionForm] = useState(defaultSessionForm);
  const [ratingDrafts, setRatingDrafts] = useState({});
  const [busyKey, setBusyKey] = useState("");
  const [profileForm, setProfileForm] = useState({
    role: user.role || "analyst",
    bio: user.bio || "",
  });
  const selectedRole = profileForm.role || user.role || "analyst";
  const roleSaved = selectedRole === user.role;

  const loadSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/sessions", {
        credentials: "include",
      });
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Could not load sessions.");
      }

      setSessions(data);
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    setProfileForm({
      role: user.role || "analyst",
      bio: user.bio || "",
    });
  }, [user.bio, user.role]);

  const sections = useMemo(
    () => [
      { key: "live", label: "Active Panels", empty: "No live panels yet." },
      { key: "scheduled", label: "Upcoming Panels", empty: "No upcoming panels yet." },
      { key: "completed", label: "Completed Panels", empty: "No completed panels yet." },
    ],
    []
  );

  const groupedSessions = useMemo(
    () =>
      sections.map((section) => ({
        ...section,
        items: sessions.filter((session) => session.status === section.key),
      })),
    [sections, sessions]
  );

  const summary = useMemo(() => {
    const live = sessions.filter((session) => session.status === "live").length;
    const scheduled = sessions.filter((session) => session.status === "scheduled").length;
    const joined = sessions.filter((session) => session.joined).length;

    return {
      live,
      scheduled,
      joined,
      total: sessions.length,
    };
  }, [sessions]);

  const updateSessionForm = (field, value) => {
    setSessionForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleProfileSave = async (event) => {
    event.preventDefault();
    setSavingProfile(true);
    setError("");

    try {
      const response = await fetch("/api/onboarding", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          role: profileForm.role,
          bio: profileForm.bio,
          rules_accepted: true,
        }),
      });
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Profile update failed.");
      }

      await onUserRefresh();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSavingProfile(false);
    }
  };

  const handleCreateSession = async (event) => {
    event.preventDefault();
    setCreating(true);
    setError("");

    try {
      const response = await fetch("/api/sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          topic: sessionForm.topic,
          description: sessionForm.description,
          scheduled_time: new Date(sessionForm.scheduledTime).toISOString(),
          duration_minutes: Number(sessionForm.durationMinutes),
          max_participants: Number(sessionForm.maxParticipants),
        }),
      });
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(data.detail || data.message || "Session creation failed.");
      }

      setSessionForm(defaultSessionForm);
      setSessions((current) => {
        const next = [data, ...current];
        return next.sort(
          (left, right) =>
            new Date(left.scheduledTime).getTime() - new Date(right.scheduledTime).getTime()
        );
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setCreating(false);
    }
  };

  const runSessionAction = async (path, options = {}) => {
    setBusyKey(path);
    setError("");
    try {
      const response = await fetch(path, {
        credentials: "include",
        ...options,
      });
      const data = await readApiResponse(response);

      if (!response.ok) {
        throw new Error(data.detail || data.message || "The action could not be completed.");
      }

      setSessions((current) =>
        current.map((session) => (session.id === data.id ? data : session))
      );
      return data;
    } catch (requestError) {
      setError(requestError.message);
      return null;
    } finally {
      setBusyKey("");
    }
  };

  const handleJoin = (sessionId) =>
    runSessionAction(`/api/sessions/${sessionId}/join`, { method: "POST" });
  const handleLeave = (sessionId) =>
    runSessionAction(`/api/sessions/${sessionId}/leave`, { method: "POST" });

  const handleRemoveParticipant = async (sessionId, participantUserId) => {
    const reason = window.prompt("Reason for removal", "Unprofessional behavior");
    if (reason === null) {
      return;
    }

    await runSessionAction(`/api/sessions/${sessionId}/remove/${participantUserId}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason }),
    });
  };

  const setRatingDraft = (sessionId, userId, field, value) => {
    const key = `${sessionId}:${userId}`;
    setRatingDrafts((current) => ({
      ...current,
      [key]: {
        ...(current[key] || {}),
        [field]: value,
      },
    }));
  };

  const handleRate = async (sessionId, target) => {
    const key = `${sessionId}:${target.userId}`;
    const draft = ratingDrafts[key] || {};
    const score = Number(draft.score || target.existingScore || 5);
    const feedback = draft.feedback ?? target.existingFeedback ?? "";

    const result = await runSessionAction(`/api/sessions/${sessionId}/ratings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        rated_user_id: target.userId,
        score,
        feedback,
      }),
    });

    if (result) {
      await onUserRefresh();
    }
  };

  return (
    <main className="dashboard-shell">
      <section className="dashboard-hero dashboard-hero--welcome">
        <div className="dashboard-hero__copy">
          <span className="eyebrow">Welcome Dashboard</span>
          <h1>Welcome back, {user.name}.</h1>
          <p className="dashboard-hero__summary">
            CricCircle is your professional cricket discussion space. Choose how
            you want to participate today, review active panels, and jump into
            rooms that still have open slots.
          </p>
          <p className="supporting-copy">
            Current role: <strong>{formatRole(user.role)}</strong> | Selected workflow:{" "}
            <strong>{formatRole(selectedRole)}</strong> | Rating:{" "}
            <strong>{user.averageRating}</strong> from <strong>{user.ratingsCount}</strong> reviews
          </p>
        </div>

        <div className="hero-actions">
          <button className="button button--ghost" onClick={loadSessions}>
            Refresh panels
          </button>
          <button className="button button--ghost" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </section>

      {error ? <p className="status status--error">{error}</p> : null}

      <section className="dashboard-overview">
        <div className="panel-card dashboard-role-card">
          <div className="dashboard-card__header">
            <div>
              <span className="eyebrow">Choose your role</span>
              <h2>How do you want to join today?</h2>
            </div>
          </div>

          <form className="session-form" onSubmit={handleProfileSave}>
            <div className="role-grid role-grid--dashboard">
              <label className={`role-card ${profileForm.role === "moderator" ? "role-card--selected" : ""}`}>
                <input
                  checked={profileForm.role === "moderator"}
                  className="visually-hidden"
                  name="dashboard-role"
                  onChange={() =>
                    setProfileForm((current) => ({ ...current, role: "moderator" }))
                  }
                  type="radio"
                  value="moderator"
                />
                <strong>Moderator</strong>
                <span>Host panels, publish topics, and manage discussion quality.</span>
              </label>

              <label className={`role-card ${profileForm.role === "analyst" ? "role-card--selected" : ""}`}>
                <input
                  checked={profileForm.role === "analyst"}
                  className="visually-hidden"
                  name="dashboard-role"
                  onChange={() =>
                    setProfileForm((current) => ({ ...current, role: "analyst" }))
                  }
                  type="radio"
                  value="analyst"
                />
                <strong>Analyst</strong>
                <span>Join panels, present your take, and build a credible profile.</span>
              </label>
            </div>

            <label className="field">
              <span>Professional bio</span>
              <textarea
                maxLength={300}
                onChange={(event) =>
                  setProfileForm((current) => ({
                    ...current,
                    bio: event.target.value,
                  }))
                }
                placeholder="Tell the community what kind of cricket conversations you want to lead or join."
                rows="4"
                value={profileForm.bio}
              />
            </label>

            <div className="inline-actions">
              <button className="button button--primary" disabled={savingProfile} type="submit">
                {savingProfile ? "Saving..." : `Use ${formatRole(selectedRole)} workflow`}
              </button>
              {!roleSaved ? (
                <span className="note">Save once to switch your account into this workflow.</span>
              ) : null}
            </div>
          </form>
        </div>

        <div className="dashboard-summary-grid">
          <div className="panel-card metric-card">
            <span className="metric-card__label">Active panels</span>
            <strong>{summary.live}</strong>
            <p>Panels happening right now.</p>
          </div>
          <div className="panel-card metric-card">
            <span className="metric-card__label">Upcoming panels</span>
            <strong>{summary.scheduled}</strong>
            <p>Rooms queued for later discussion.</p>
          </div>
          <div className="panel-card metric-card">
            <span className="metric-card__label">Your joined rooms</span>
            <strong>{summary.joined}</strong>
            <p>Panels where you already hold a seat.</p>
          </div>
          <div className="panel-card metric-card">
            <span className="metric-card__label">Total panels</span>
            <strong>{summary.total}</strong>
            <p>All rooms currently visible in the lobby.</p>
          </div>
        </div>
      </section>

      <section className="dashboard-overview">
        {selectedRole === "moderator" ? (
          <div className="panel-card moderator-studio">
            <div className="dashboard-card__header">
              <div>
                <span className="eyebrow">Moderator Studio</span>
                <h2>Moderator workflow</h2>
              </div>
              <p className="supporting-copy">
                Create panels, manage participation, and lead the room professionally.
              </p>
            </div>

            {!roleSaved ? (
              <p className="note note--block">
                Save the moderator workflow above first, then create the panel. CricCircle will
                generate the Google Meet link automatically.
              </p>
            ) : null}

            <form className="session-form" onSubmit={handleCreateSession}>
              <div className="session-form__grid">
                <label className="field">
                  <span>Topic</span>
                  <input
                    onChange={(event) => updateSessionForm("topic", event.target.value)}
                    placeholder="Who owns the death overs in IPL pressure games?"
                    required
                    value={sessionForm.topic}
                  />
                </label>
              </div>

              <label className="field">
                <span>Discussion brief</span>
                <textarea
                  onChange={(event) => updateSessionForm("description", event.target.value)}
                  placeholder="Explain the angle, expected debate, and what analysts should prepare."
                  rows="4"
                  value={sessionForm.description}
                />
              </label>

              <div className="session-form__grid">
                <label className="field">
                  <span>Start time</span>
                  <input
                    min={new Date().toISOString().slice(0, 16)}
                    onChange={(event) => updateSessionForm("scheduledTime", event.target.value)}
                    required
                    type="datetime-local"
                    value={sessionForm.scheduledTime}
                  />
                </label>

                <label className="field">
                  <span>Total duration (minutes)</span>
                  <input
                    max="180"
                    min="15"
                    onChange={(event) => updateSessionForm("durationMinutes", event.target.value)}
                    required
                    type="number"
                    value={sessionForm.durationMinutes}
                  />
                </label>

                <label className="field">
                  <span>Slots</span>
                  <input
                    max="12"
                    min="2"
                    onChange={(event) => updateSessionForm("maxParticipants", event.target.value)}
                    required
                    type="number"
                    value={sessionForm.maxParticipants}
                  />
                </label>
              </div>

              <button
                className="button button--primary"
                disabled={creating || !roleSaved}
                type="submit"
              >
                {creating ? "Publishing..." : "Create panel"}
              </button>
            </form>
          </div>
        ) : (
          <div className="panel-card moderator-studio">
            <div className="dashboard-card__header">
              <div>
                <span className="eyebrow">Analyst View</span>
                <h2>Analyst workflow</h2>
              </div>
            </div>
            <p className="supporting-copy">
              Review active panels, check slot availability, join the rooms that
              fit your cricket angle, and build credibility through ratings.
            </p>
            <ul className="feature-list">
              <li>Browse active and upcoming panels from the lobby below.</li>
              <li>Watch the available slot count before joining.</li>
              <li>Use the panel timing and duration left to plan your entry.</li>
            </ul>
          </div>
        )}

        <div className="panel-card quick-notes">
          <div className="dashboard-card__header">
            <div>
              <span className="eyebrow">
                {selectedRole === "moderator" ? "Moderator Notes" : "Analyst Notes"}
              </span>
              <h2>
                {selectedRole === "moderator"
                  ? "What a moderator can do"
                  : "What an analyst can do"}
              </h2>
            </div>
          </div>
          {selectedRole === "moderator" ? (
            <ul className="feature-list">
              <li>Create a panel with topic, slots, timing, and meeting link.</li>
              <li>Track which analysts already joined each live discussion.</li>
              <li>Remove disruptive analysts immediately from your panel.</li>
              <li>Build your hosting reputation through post-session ratings.</li>
            </ul>
          ) : (
            <ul className="feature-list">
              <li>Compare live panels using available slots and duration left.</li>
              <li>Join only the panels where your cricket take adds value.</li>
              <li>Meeting links unlock after you take a seat in the panel.</li>
              <li>Rate moderators and fellow analysts after the session ends.</li>
            </ul>
          )}
        </div>
      </section>

      <section className="session-board">
        {loading ? <div className="panel-card">Loading panel dashboard...</div> : null}

        {!loading &&
          groupedSessions.map((section) => (
            <div className="session-section" key={section.key}>
              <div className="section-heading">
                <h2>{section.label}</h2>
                <span>{section.items.length} panel(s)</span>
              </div>

              {section.items.length === 0 ? (
                <div className="empty-state">
                  <p>{section.empty}</p>
                </div>
              ) : (
                <div className="session-grid">
                  {section.items.map((session, index) => (
                    <article className="session-card session-card--detailed" key={session.id}>
                      <div className="session-card__header">
                        <span className={`pill pill--${session.status}`}>{session.status}</span>
                        <span className="session-time">{formatDate(session.scheduledTime)}</span>
                      </div>

                      <div className="session-card__titleblock">
                        <span className="session-kicker">Panel {index + 1}</span>
                        <h3>Discussion {session.id}</h3>
                        <p className="session-description">
                          Topic: {session.topic}
                        </p>
                      </div>

                      <dl className="session-meta session-meta--grid">
                        <div>
                          <dt>Moderator</dt>
                          <dd>
                            {session.host.name} | {session.host.averageRating} / 5
                          </dd>
                        </div>
                        <div>
                          <dt>Slots</dt>
                          <dd>{session.maxParticipants}</dd>
                        </div>
                        <div>
                          <dt>Available slots</dt>
                          <dd>
                            {session.slotsLeft}/{session.maxParticipants}
                          </dd>
                        </div>
                        <div>
                          <dt>Total duration</dt>
                          <dd>{session.durationMinutes} min</dd>
                        </div>
                        <div>
                          <dt>Duration left</dt>
                          <dd>{formatDurationLeft(session)}</dd>
                        </div>
                        <div>
                          <dt>Joined count</dt>
                          <dd>
                            {session.joinedCount}/{session.maxParticipants}
                          </dd>
                        </div>
                      </dl>

                      {session.description ? (
                        <p className="note note--block">{session.description}</p>
                      ) : null}

                      <div className="inline-actions inline-actions--tight">
                        {!session.isHost && !session.joined && session.status !== "completed" ? (
                          <button
                            className="button button--primary"
                            disabled={busyKey === `/api/sessions/${session.id}/join`}
                            onClick={() => handleJoin(session.id)}
                          >
                            Join panel
                          </button>
                        ) : null}

                        {session.joined ? (
                          <button
                            className="button button--ghost"
                            disabled={busyKey === `/api/sessions/${session.id}/leave`}
                            onClick={() => handleLeave(session.id)}
                          >
                            Leave panel
                          </button>
                        ) : null}

                        {session.meetingLink ? (
                          <a
                            className="button button--secondary"
                            href={session.meetingLink}
                            rel="noreferrer"
                            target="_blank"
                          >
                            Open meeting
                          </a>
                        ) : null}
                      </div>

                      {session.meetingLinkLocked ? (
                        <p className="note">Meeting link unlocks once you join the panel.</p>
                      ) : null}

                      <div className="participant-block">
                        <h4>Analysts in this panel</h4>
                        {session.participants.length === 0 ? (
                          <p className="note">No analysts have joined yet.</p>
                        ) : (
                          <ul className="participant-list">
                            {session.participants.map((participant) => (
                              <li key={`${session.id}-${participant.id}`}>
                                <div>
                                  <strong>{participant.name}</strong>
                                  <span>
                                    {participant.role} | {participant.averageRating} / 5
                                  </span>
                                </div>
                                {session.canManage ? (
                                  <button
                                    className="text-button"
                                    onClick={() =>
                                      handleRemoveParticipant(session.id, participant.id)
                                    }
                                  >
                                    Remove
                                  </button>
                                ) : null}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>

                      {session.ratingTargets.length > 0 ? (
                        <div className="rating-block">
                          <h4>Post-session ratings</h4>
                          {session.ratingTargets.map((target) => {
                            const key = `${session.id}:${target.userId}`;
                            const draft = ratingDrafts[key] || {};
                            return (
                              <div className="rating-card" key={key}>
                                <div>
                                  <strong>{target.name}</strong>
                                  <span>{target.role}</span>
                                </div>
                                <div className="rating-controls">
                                  <select
                                    onChange={(event) =>
                                      setRatingDraft(
                                        session.id,
                                        target.userId,
                                        "score",
                                        event.target.value
                                      )
                                    }
                                    value={draft.score || target.existingScore || 5}
                                  >
                                    {[5, 4, 3, 2, 1].map((score) => (
                                      <option key={score} value={score}>
                                        {score} / 5
                                      </option>
                                    ))}
                                  </select>
                                  <input
                                    onChange={(event) =>
                                      setRatingDraft(
                                        session.id,
                                        target.userId,
                                        "feedback",
                                        event.target.value
                                      )
                                    }
                                    placeholder="Professional note"
                                    value={draft.feedback ?? target.existingFeedback ?? ""}
                                  />
                                  <button
                                    className="button button--ghost"
                                    disabled={busyKey === `/api/sessions/${session.id}/ratings`}
                                    onClick={() => handleRate(session.id, target)}
                                    type="button"
                                  >
                                    Save
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : null}
                    </article>
                  ))}
                </div>
              )}
            </div>
          ))}
      </section>
    </main>
  );
}

function formatDate(value) {
  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function formatRole(role) {
  return role === "moderator" ? "Moderator" : "Analyst";
}

function formatDurationLeft(session) {
  if (session.status === "scheduled") {
    return "Starts soon";
  }
  if (session.status === "completed") {
    return "Ended";
  }

  const start = new Date(session.scheduledTime).getTime();
  const end = start + session.durationMinutes * 60 * 1000;
  const remainingMs = end - Date.now();

  if (remainingMs <= 0) {
    return "Ending now";
  }

  const totalMinutes = Math.ceil(remainingMs / 60000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${totalMinutes} min`;
}

async function readApiResponse(response) {
  const text = await response.text();

  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch {
    return {
      message: text,
    };
  }
}

export default Dashboard;
