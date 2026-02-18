import { useState } from "react";

export default function LoginModal({ onLogin }) {
  const [name, setName] = useState("");

  const handleLogin = () => {
    if (!name.trim()) return;
    localStorage.setItem("username", name);
    onLogin(name);
  };

  return (
    <div className="login-overlay">
      <div className="login-card">
        <h1>Welcome back 👋</h1>
        <p>Enter your name to continue</p>

        <input
          placeholder="Your name..."
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleLogin()}
        />

        <button onClick={handleLogin}>Continue</button>
      </div>
    </div>
  );
}
