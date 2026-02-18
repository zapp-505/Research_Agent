export default function InputBar({ input, setInput, onSend }) {
  return (
    <div className="input-area">
      <div className="input-inner">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything..."
          onKeyDown={(e) => e.key === "Enter" && onSend()}
        />
        <button onClick={onSend}>Send</button>
      </div>
    </div>
  );
}
