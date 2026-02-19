export default function Topbar({ username, onLogout }) {
  return (
    <div className="topbar">
      <div className="brand">Research AI</div>

      <div className="profile" onClick={onLogout}>
        <div className="avatar">👤</div>
        <span>{username}</span>
      </div>
    </div>
  );
}
