import { useState, useEffect, useRef, useCallback } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import AgentStatus from "./components/AgentStatus";
import ClarificationModal from "./components/ClarificationModal";
import "./App.css";
import {
  getDefaultMessages,
  NEW_CHAT_MESSAGE,
  hasUserMessages,
  deriveTitle,
  loadConversations,
  upsertConversation,
  removeConversation,
  buildConversationEntry,
} from "./utils/chatHistory";

const API_URL = "http://localhost:8000";

export default function App() {
  const [threadId, setThreadId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState(getDefaultMessages);
  const [conversations, setConversations] = useState(() => loadConversations());
  const createdAtRef = useRef(Date.now());

  const [isLoading, setIsLoading] = useState(false);
  const [waitingForClarification, setWaitingForClarification] = useState(false);
  const [clarificationQuestion, setClarificationQuestion] = useState("");
  const [agentSteps, setAgentSteps] = useState([]);
  const [currentAgent, setCurrentAgent] = useState("");
  const [backendOnline, setBackendOnline] = useState(true);

  const activeTitle = hasUserMessages(messages)
    ? deriveTitle(messages)
    : "New conversation";

  const persistCurrentChat = useCallback(() => {
    if (!hasUserMessages(messages)) return;
    const entry = buildConversationEntry({
      threadId,
      messages,
      createdAt: createdAtRef.current,
    });
    setConversations((prev) => upsertConversation(prev, entry));
  }, [messages, threadId]);

  useEffect(() => {
    persistCurrentChat();
  }, [persistCurrentChat]);

  const clearSessionState = () => {
    setAgentSteps([]);
    setWaitingForClarification(false);
    setClarificationQuestion("");
    setIsLoading(false);
    setCurrentAgent("");
  };

  const addAgentStep = (step) => {
    setAgentSteps((prev) => [...prev, step]);
  };

  const sendQuery = async (userMessage) => {
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setAgentSteps([]);
    setIsLoading(true);
    setCurrentAgent("Clarity Agent");

    try {
      const response = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMessage, thread_id: threadId }),
      });

      const data = await response.json();
      setBackendOnline(true);

      if (data.status === "complete") {
        addAgentStep("Clarity Agent: clear");
        addAgentStep("Research Agent: complete");
        addAgentStep("Validator Agent: sufficient");
        addAgentStep("Synthesis Agent: answer ready");
        setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
        setWaitingForClarification(false);
      } else if (data.status === "needs_clarification") {
        addAgentStep("Clarity Agent: needs clarification");
        setWaitingForClarification(true);
        setClarificationQuestion(data.question);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${data.message || "Something went wrong. Please try again."}`,
          },
        ]);
      }
    } catch {
      setBackendOnline(false);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Cannot connect to the backend. Start FastAPI on port 8000, then try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
      setCurrentAgent("");
    }
  };

  const sendClarification = async (answer) => {
    setMessages((prev) => [...prev, { role: "user", content: answer }]);
    setWaitingForClarification(false);
    setIsLoading(true);
    setCurrentAgent("Research Agent");
    addAgentStep("Clarification received");

    try {
      const response = await fetch(`${API_URL}/clarify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer, thread_id: threadId }),
      });

      const data = await response.json();
      setBackendOnline(true);

      if (data.status === "complete") {
        addAgentStep("Research Agent: complete");
        addAgentStep("Synthesis Agent: answer ready");
        setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Error: ${data.message || "Something went wrong."}`,
          },
        ]);
      }
    } catch {
      setBackendOnline(false);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Cannot connect to the backend." },
      ]);
    } finally {
      setIsLoading(false);
      setCurrentAgent("");
    }
  };

  const startNewConversation = async () => {
    if (isLoading) return;

    persistCurrentChat();

    try {
      const response = await fetch(`${API_URL}/reset`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ thread_id: threadId }),
      });
      const data = await response.json();
      setThreadId(data.new_thread_id);
      setBackendOnline(true);
    } catch {
      setThreadId(crypto.randomUUID());
    }

    createdAtRef.current = Date.now();
    setMessages([NEW_CHAT_MESSAGE]);
    clearSessionState();
  };

  const selectConversation = (chat) => {
    if (isLoading || chat.threadId === threadId) return;

    if (hasUserMessages(messages)) {
      const entry = buildConversationEntry({
        threadId,
        messages,
        createdAt: createdAtRef.current,
      });
      setConversations((prev) => upsertConversation(prev, entry));
    }

    setThreadId(chat.threadId);
    setMessages(chat.messages);
    createdAtRef.current = chat.createdAt || Date.now();
    clearSessionState();
  };

  const deleteConversation = (id) => {
    const next = removeConversation(conversations, id);
    setConversations(next);

    if (id === threadId) {
      const newId = crypto.randomUUID();
      createdAtRef.current = Date.now();
      setThreadId(newId);
      setMessages(getDefaultMessages());
      clearSessionState();
    }
  };

  const allConversationsForSidebar = (() => {
    if (!hasUserMessages(messages)) return conversations;
    const current = buildConversationEntry({
      threadId,
      messages,
      createdAt: createdAtRef.current,
    });
    const without = conversations.filter((c) => c.id !== threadId);
    return [current, ...without].sort(
      (a, b) => (b.updatedAt || 0) - (a.updatedAt || 0)
    );
  })();

  return (
    <div className="app-container">
      <div className="ambient-layer" aria-hidden>
        <div className="ambient-orb ambient-orb--1" />
        <div className="ambient-orb ambient-orb--2" />
        <div className="ambient-grid" />
      </div>

      <Sidebar
        conversations={allConversationsForSidebar}
        activeThreadId={threadId}
        activeTitle={activeTitle}
        onSelectConversation={selectConversation}
        onDeleteConversation={deleteConversation}
        onReset={startNewConversation}
        isLoading={isLoading}
      />

      <main className="main-area">
        <header className="chat-header">
          <div className="chat-header-left">
            <div className="header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
            </div>
            <div>
              <h1>Synapse AI Research Assistant</h1>
              <p className="chat-header-topic">{activeTitle}</p>
            </div>
          </div>
          <div className="header-actions">
            <div className={`status-pill ${backendOnline ? "" : "status-pill--offline"}`}>
              <span className="status-dot" />
              {backendOnline ? "Live" : "Offline"}
            </div>
          </div>
        </header>

        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          currentAgent={currentAgent}
          waitingForClarification={waitingForClarification}
          clarificationQuestion={clarificationQuestion}
          onSendMessage={sendQuery}
          onSendClarification={sendClarification}
        />
      </main>

      <AgentStatus steps={agentSteps} currentAgent={currentAgent} isLoading={isLoading} />

      {waitingForClarification && (
        <ClarificationModal question={clarificationQuestion} onSubmit={sendClarification} />
      )}
    </div>
  );
}
