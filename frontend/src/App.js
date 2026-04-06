import "./App.css";
import Dashboard from "./Dashboard";

function App() {
  const isLoggedIn = window.location.pathname === "/dashboard";

  return (
    <>
      {isLoggedIn ? (
        <Dashboard />
      ) : (
        <div className="app">
          <header className="header">
            <h2>CricCircle 🏏</h2>
            <button
              className="login-btn"
              onClick={() => {
                window.location.href = "http://127.0.0.1:8000/login/google";
              }}
            >
              Login
            </button>
          </header>

          <div className="hero">
            <h1>Where Cricket Minds Meet</h1>
            <p>Join discussions and share insights</p>

            <button
              className="primary-btn"
              onClick={() => {
                window.location.href = "http://127.0.0.1:8000/login/google";
              }}
            >
              Get Started
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default App;