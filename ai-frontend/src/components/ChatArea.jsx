import Message from "./Message";

export default function ChatArea({ messages, typing, chatEndRef }) {
  return (
    <div className="chat-wrapper">
      <div className="chat-box">
        {messages.map((msg, i) => (
          <Message key={i} msg={msg} />
        ))}

        {typing && (
          <div className="msg-row ai">
            <div className="avatar">🤖</div>
            <div className="bubble ai typing">Thinking...</div>
          </div>
        )}

        <div ref={chatEndRef}></div>
      </div>
    </div>
  );
}
