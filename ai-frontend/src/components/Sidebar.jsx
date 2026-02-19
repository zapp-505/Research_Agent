export default function Sidebar({ chats, activeChat, onNewChat, onSwitch }) {
  return (
    <div className="sidebar">
      <h2>Chats</h2>
      <button className="new-chat-btn" onClick={onNewChat}>
        + New Chat
      </button>

      <div className="chat-list">
        {chats.map((chat, i) => (
          <div
            key={chat.id}
            className={`chat-item ${i === activeChat ? "active" : ""}`}
            onClick={() => onSwitch(i)}
          >
             {chat.title}
          </div>
        ))}
      </div>
    </div>
  );
}
