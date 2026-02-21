/**
 * Message.jsx
 * Renders a single chat message bubble.
 * AI messages support basic markdown-like rendering (bold, line breaks).
 */

function renderText(text) {
  // Convert **bold** and newlines to HTML
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\n/g, "<br/>");
}

export default function Message({ msg }) {
  return (
    <div className={`msg-row ${msg.role}`}>
      {msg.role === "ai" && <div className="avatar">✨</div>}

      <div
        className={`bubble ${msg.role}`}
        dangerouslySetInnerHTML={
          msg.role === "ai"
            ? { __html: renderText(msg.text) }
            : undefined
        }
      >
        {msg.role !== "ai" ? msg.text : undefined}
      </div>

      {msg.role === "user" && <div className="avatar">👤</div>}
    </div>
  );
}
