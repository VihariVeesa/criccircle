import { useEffect, useState } from "react";
import "./App.css";
import Dashboard from "./Dashboard";

const defaultOnboarding = {
  role: "analyst",
  bio: "",
  rulesAccepted: false,
};

function App() {
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [onboardingForm, setOnboardingForm] = useState(defaultOnboarding);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const loadUser = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/me", {
        credentials: "include",
      });

      if (response.status === 401) {
        setUser(null);
        setError("");
        return;
      }

      if (!response.ok) {
        throw new Error("We could not load your CricCircle profile.");
      }

      const data = await response.json();
      setUser(data);
      setOnboardingForm({
        role: data.role || "analyst",
        bio: data.bio || "",
        rulesAccepted: Boolean(data.rulesAccepted),
      });
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUser();
  }, []);

  const startGoogleLogin = () => {
    window.location.href = "/api/auth/google/login";
  };

  const handleLogout = async () => {
    await fetch("/api/auth/logout", {
      method: "POST",
      credentials: "include",
    });
    setUser(null);
    setOnboardingForm(defaultOnboarding);
  };

  const handleOnboardingSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const response = await fetch("/api/onboarding", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          role: onboardingForm.role,
          bio: onboardingForm.bio,
          rules_accepted: onboardingForm.rulesAccepted,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Onboarding could not be saved.");
      }

      setUser(data);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <main className="shell shell--loading">
        <div className="loading-card">
          <span className="eyebrow">CricCircle</span>
          <h1>Preparing your discussion room</h1>
        </div>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="shell">
        <section className="landing">
          <div className="landing__copy">
            <span className="eyebrow">Structured cricket conversation</span>
            <h1>Where cricket analysts earn trust, not just attention.</h1>
            <p className="landing__summary">
              CricCircle helps moderators and analysts run focused, professional
              discussions with role-based access, curated rooms, and reputation
              that grows through ratings.
            </p>
            <div className="landing__actions">
              <button className="button button--primary" onClick={startGoogleLogin}>
                Continue with Google
              </button>
              <span className="supporting-copy">
                MVP focus: onboarding, moderated sessions, ratings, and a
                replay-ready workflow.
              </span>
            </div>
          </div>

          <div className="landing__panel">
            <div className="panel-card panel-card--accent">
              <h2>What makes this different</h2>
              <ul className="feature-list">
                <li>Choose your role: moderator or analyst.</li>
                <li>Join time-bound cricket sessions with clear participant limits.</li>
                <li>Keep the tone professional through rules and moderator control.</li>
                <li>Build reputation through post-session ratings.</li>
              </ul>
            </div>
            <div className="panel-card">
              <h2>Why users stay</h2>
              <p>
                The platform identity lives here, even if recordings later reach
                YouTube. Ratings, host credibility, and analyst history remain
                native to CricCircle.
              </p>
            </div>
          </div>
        </section>
        {error ? <p className="status status--error">{error}</p> : null}
      </main>
    );
  }

  if (!user.onboardingComplete) {
    return (
      <main className="shell">
        <section className="onboarding-card">
          <span className="eyebrow">Welcome, {user.name}</span>
          <h1>Set up your place in CricCircle</h1>
          <p className="supporting-copy">
            Everyone signs in with Google first. Then we place them into the
            platform as a moderator or analyst and lock in the professional code
            of conduct.
          </p>

          <form className="onboarding-form" onSubmit={handleOnboardingSubmit}>
            <div className="role-grid">
              <label className={`role-card ${onboardingForm.role === "moderator" ? "role-card--selected" : ""}`}>
                <input
                  checked={onboardingForm.role === "moderator"}
                  className="visually-hidden"
                  name="role"
                  onChange={() =>
                    setOnboardingForm((current) => ({ ...current, role: "moderator" }))
                  }
                  type="radio"
                  value="moderator"
                />
                <strong>Moderator</strong>
                <span>Host panels, shape topics, and manage room discipline.</span>
              </label>

              <label className={`role-card ${onboardingForm.role === "analyst" ? "role-card--selected" : ""}`}>
                <input
                  checked={onboardingForm.role === "analyst"}
                  className="visually-hidden"
                  name="role"
                  onChange={() =>
                    setOnboardingForm((current) => ({ ...current, role: "analyst" }))
                  }
                  type="radio"
                  value="analyst"
                />
                <strong>Analyst</strong>
                <span>Join discussion rooms, present viewpoints, and earn ratings.</span>
              </label>
            </div>

            <label className="field">
              <span>Professional bio</span>
              <textarea
                maxLength={300}
                onChange={(event) =>
                  setOnboardingForm((current) => ({
                    ...current,
                    bio: event.target.value,
                  }))
                }
                placeholder="Tell the community what kind of cricket conversations you enjoy most."
                rows="4"
                value={onboardingForm.bio}
              />
            </label>

            <label className="checkbox">
              <input
                checked={onboardingForm.rulesAccepted}
                onChange={(event) =>
                  setOnboardingForm((current) => ({
                    ...current,
                    rulesAccepted: event.target.checked,
                  }))
                }
                type="checkbox"
              />
              <span>
                I agree to keep my discussions professional. Abusive language,
                personal attacks, and disruptive behavior can lead to removal.
              </span>
            </label>

            {error ? <p className="status status--error">{error}</p> : null}

            <div className="inline-actions">
              <button className="button button--primary" disabled={submitting} type="submit">
                {submitting ? "Saving..." : "Enter CricCircle"}
              </button>
              <button className="button button--ghost" onClick={handleLogout} type="button">
                Sign out
              </button>
            </div>
          </form>
        </section>
      </main>
    );
  }

  return (
    <Dashboard
      onLogout={handleLogout}
      onUserRefresh={loadUser}
      user={user}
    />
  );
}

export default App;
