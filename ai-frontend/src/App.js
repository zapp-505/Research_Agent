import { useState, useRef, useEffect } from "react";
import "./App.css";

import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import ChatArea from "./components/ChatArea";
import InputBar from "./components/InputBar";
import LoginModal from "./components/LoginModal";

export default function App() {
  // ================= LOGIN =================
  const [username, setUsername] = useState(
    localStorage.getItem("username")
  );

  const logout = () => {
    localStorage.removeItem("username");
    setUsername(null);
    setChats([]);
    setMessages([]);
  };

  // ================= CHAT STATES =================
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [typing, setTyping] = useState(false);

  const [chats, setChats] = useState([]);
  const [activeChat, setActiveChat] = useState(0);

  const chatEndRef = useRef(null);

  // ================= LOAD CHATS PER USER =================
  useEffect(() => {
    if (username) {
      const saved = localStorage.getItem(`chats_${username}`);
      const userChats = saved
        ? JSON.parse(saved)
        : [{ id: 1, title: "New Chat", messages: [] }];

      setChats(userChats);
      setActiveChat(0);
      setMessages(userChats[0]?.messages || []);
    }
  }, [username]);

  // ================= SAVE CHATS PER USER =================
  useEffect(() => {
    if (username && chats.length) {
      localStorage.setItem(
        `chats_${username}`,
        JSON.stringify(chats)
      );
    }
  }, [chats, username]);

  // ================= GENERATE CHAT TITLE =================
  const generateTitle = (text) => {
    const words = text.split(" ").slice(0, 4).join(" ");
    return words + (text.split(" ").length > 4 ? "..." : "");
  };

  // ================= SEND MESSAGE =================
  const sendMessage = () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", text: input };
    const updated = [...messages, userMsg];
    setMessages(updated);

    const newChats = [...chats];

    // Update title if first message
    if (messages.length === 0) {
      newChats[activeChat].title = generateTitle(input);
    }

    newChats[activeChat].messages = updated;
    setChats(newChats);

    setInput("");
    setTyping(true);

    setTimeout(() => {
      const botMsg = {
        role: "ai",
        text: `Hi ${username}! Your chats are now saved per user ✨`,
      };

      const newMsgs = [...updated, botMsg];
      setMessages(newMsgs);

      const updatedChats = [...newChats];
      updatedChats[activeChat].messages = newMsgs;
      setChats(updatedChats);

      setTyping(false);
    }, 900);
  };

  // ================= NEW CHAT =================
  const newChat = () => {
    const newChats = [
      ...chats,
      { id: Date.now(), title: "New Chat", messages: [] },
    ];
    setChats(newChats);
    setActiveChat(newChats.length - 1);
    setMessages([]);
  };

  // ================= SWITCH CHAT =================
  const switchChat = (i) => {
    setActiveChat(i);
    setMessages(chats[i].messages);
  };

  // ================= AUTO SCROLL =================
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

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

        {/* Chat */}
        <ChatArea
          messages={messages}
          typing={typing}
          chatEndRef={chatEndRef}
        />

        {/* Input */}
        <InputBar
          input={input}
          setInput={setInput}
          onSend={sendMessage}
        />
      </div>

      {/* Login Popup */}
      {!username && <LoginModal onLogin={setUsername} />}
    </div>
  );
}
