export default function Message({ msg }) {
  return (
    <div className={`msg-row ${msg.role}`}>
      {msg.role === "ai" && <div className="avatar">✨
</div>}

      <div className={`bubble ${msg.role}`}>
        {msg.text}
      </div>

      {msg.role === "user" && <div className="avatar">👤</div>}
    </div>
  );
}
