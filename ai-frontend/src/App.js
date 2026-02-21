import { useState, useRef, useEffect } from "react";
import "./App.css";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import ChatArea from "./components/ChatArea";
import InputBar from "./components/InputBar";
import LoginModal from "./components/LoginModal";

const API_BASE = "http://localhost:8000";

export default function App() {
  // ================= LOGIN =================
  const [username, setUsername] = useState(localStorage.getItem("username"));

  const logout = () => {
    localStorage.removeItem("username");
    setUsername(null);
    setChats([]);
    setMessages([]);
    setThreadId(null);
    setAgentPhase("idle");
  };

  // ================= CHAT STATES =================
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [typing, setTyping] = useState(false);

  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(0);

  // ── Agent state ──────────────────────────────────────────────────────────────
  // threadId: the LangGraph thread we're talking to for the current chat
  // agentPhase: "idle" | "waiting" | "complete"
  const [threadId, setThreadId] = useState(null);
  const [agentPhase, setAgentPhase] = useState("idle");

  const chatEndRef = useRef(null);

  // ================= LOAD CHATS PER USER =================
  useEffect(() => {
    if (username) {
      const saved = localStorage.getItem(`chats_${username}`);
      const userChats = saved
        ? JSON.parse(saved)
        : [{ id: 1, title: "New Chat", messages: [], threadId: null }];
      setChats(userChats);
      setActiveChat(0);
      setMessages(userChats[0]?.messages || []);
      setThreadId(userChats[0]?.threadId || null);
      setAgentPhase(userChats[0]?.threadId ? "waiting" : "idle");
    }
  }, [username]);

  // ================= SAVE CHATS PER USER =================
  useEffect(() => {
    if (username && chats.length) {
      localStorage.setItem(`chats_${username}`, JSON.stringify(chats));
    }
  }, [chats, username]);

  // ================= GENERATE CHAT TITLE =================
  const generateTitle = (text) => {
    const words = text.split(" ").slice(0, 4).join(" ");
    return words + (text.split(" ").length > 4 ? "..." : "");
  };

  // ================= HELPER: append messages & sync to chats ==================
  const appendMessages = (newMsgs, updatedThreadId = threadId) => {
    setMessages((prev) => {
      const updated = [...prev, ...newMsgs];
      setChats((prevChats) => {
        const next = [...prevChats];
        next[activeChat] = {
          ...next[activeChat],
          messages: updated,
          threadId: updatedThreadId,
        };
        return next;
      });
      return updated;
    });
  };

  // ================= HANDLE AI RESPONSE from API ==============================
  const handleAgentResponse = (data, userText, isFirstMessage) => {
    setTyping(false);

    if (data.status === "error") {
      appendMessages([{ role: "ai", text: "⚠️ Error: " + data.message }]);
      setAgentPhase("idle");
      return;
    }

    // Update thread tracking
    const newThreadId = data.thread_id;
    setThreadId(newThreadId);

    // Update chat title on first message
    if (isFirstMessage) {
      setChats((prev) => {
        const next = [...prev];
        next[activeChat] = {
          ...next[activeChat],
          title: generateTitle(userText),
          threadId: newThreadId,
        };
        return next;
      });
    }

    if (data.status === "waiting") {
      // Agent is paused waiting for user to confirm the interpretation
      appendMessages(
        [{ role: "ai", text: data.message }],
        newThreadId
      );
      setAgentPhase("waiting");
    } else if (data.status === "complete") {
      // Agent finished — display the research output
      appendMessages(
        [{ role: "ai", text: data.message }],
        newThreadId
      );
      setAgentPhase("complete");
    }
  };

  // ================= SEND MESSAGE =================
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userText = input.trim();
    setInput("");

    // Append the user message immediately
    const userMsg = { role: "user", text: userText };
    const isFirstMessage = messages.length === 0;

    setMessages((prev) => {
      const updated = [...prev, userMsg];
      setChats((prevChats) => {
        const next = [...prevChats];
        next[activeChat] = { ...next[activeChat], messages: updated };
        return next;
      });
      return updated;
    });

    setTyping(true);

    try {
      let response;

      if (agentPhase === "idle" || agentPhase === "complete") {
        // ── First message or new topic: start a fresh agent run ──────────────
        const res = await fetch(`${API_BASE}/chat/start`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: userText }),
        });
        response = await res.json();
      } else if (agentPhase === "waiting") {
        // ── Agent is waiting for confirmation/corrections ─────────────────────
        const res = await fetch(`${API_BASE}/chat/resume`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            thread_id: threadId,
            user_response: userText,
          }),
        });
        response = await res.json();
      }

      handleAgentResponse(response, userText, isFirstMessage);
    } catch (err) {
      setTyping(false);
      appendMessages([
        {
          role: "ai",
          text: "⚠️ Could not reach the backend. Is the API server running on port 8000?",
        },
      ]);
    }
  };

  // ================= NEW CHAT =================
  const newChat = () => {
    const newChats = [
      ...chats,
      { id: Date.now(), title: "New Chat", messages: [], threadId: null },
    ];
    setChats(newChats);
    setActiveChat(newChats.length - 1);
    setMessages([]);
    setThreadId(null);
    setAgentPhase("idle");
  };

  // ================= SWITCH CHAT =================
  const switchChat = (i) => {
    setActiveChat(i);
    setMessages(chats[i].messages || []);
    setThreadId(chats[i].threadId || null);
    // If the chat has a threadId it was mid-conversation → "waiting"
    setAgentPhase(chats[i].threadId ? "waiting" : "idle");
  };

  // ================= AUTO SCROLL =================
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  // ================= STATUS HINT =================
  const statusHint =
    agentPhase === "waiting"
      ? "💬 Agent is awaiting your confirmation or correction..."
      : agentPhase === "complete"
      ? "✅ Research complete. Start a new chat or ask a follow-up."
      : "";

  // ================= UI =================
  return (
    <div className="app">
      {/* Sidebar */}
      <Sidebar
        chats={chats}
        activeChat={activeChat}
        onNewChat={newChat}
        onSwitch={switchChat}
      />

      <div className="main">
        {/* Topbar */}
        <Topbar username={username} onLogout={logout} />

        {/* Status hint bar */}
        {statusHint && (
          <div
            style={{
              padding: "6px 20px",
              fontSize: "0.78rem",
              color: "#a3e635",
              background: "rgba(163,230,53,0.07)",
              borderBottom: "1px solid rgba(163,230,53,0.15)",
            }}
          >
            {statusHint}
          </div>
        )}

        {/* Chat */}
        <ChatArea messages={messages} typing={typing} chatEndRef={chatEndRef} />

        {/* Input */}
        <InputBar input={input} setInput={setInput} onSend={sendMessage} />
      </div>

      {/* Login Popup */}
      {!username && <LoginModal onLogin={setUsername} />}
    </div>
  );
}
