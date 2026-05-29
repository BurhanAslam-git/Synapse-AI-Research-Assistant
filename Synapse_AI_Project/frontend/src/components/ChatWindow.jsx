import { useState, useRef, useEffect } from "react";

const SUGGESTIONS = [
  { label: "Earnings", text: "What were Tesla's key Q4 2025 financial highlights?" },
  { label: "Compare", text: "Compare Apple vs Microsoft market position in 2025" },
  { label: "Deep dive", text: "Summarize NVIDIA's recent earnings and growth outlook" },
  { label: "Quick scan", text: "Give me an overview of Amazon's business segments" },
];

function BotAvatar() {
  return (
    <div className="avatar avatar--bot" aria-hidden>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
      </svg>
    </div>
  );
}

function UserAvatar() {
  return (
    <div className="avatar avatar--user" aria-hidden>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
    </div>
  );
}

function WelcomeHero({ onSuggestion }) {
  return (
    <section className="welcome-hero">
      <div className="welcome-badge">
        <span className="welcome-badge-dot" />
        Multi-agent research
      </div>
      <h2 className="welcome-title">Ask anything about any company</h2>
      <p className="welcome-subtitle">
        Synapse routes your question through clarity, research, validation, and synthesis agents —
        then returns a polished, evidence-backed answer.
      </p>
      <div className="suggestion-grid">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            type="button"
            className="suggestion-chip"
            onClick={() => onSuggestion(s.text)}
          >
            <div className="suggestion-chip-label">{s.label}</div>
            <div className="suggestion-chip-text">{s.text}</div>
          </button>
        ))}
      </div>
    </section>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <article className={`message-row ${isUser ? "message-row--user" : ""}`}>
      {!isUser && <BotAvatar />}
      <div>
        <div className={`message-bubble ${isUser ? "message-bubble--user" : "message-bubble--assistant"}`}>
          {message.content}
        </div>
        <div className="message-meta">{isUser ? "You" : "Synapse AI"}</div>
      </div>
      {isUser && <UserAvatar />}
    </article>
  );
}

function TypingIndicator({ currentAgent }) {
  return (
    <div className="typing-row">
      <BotAvatar />
      <div className="typing-bubble">
        <span className="typing-label">{currentAgent || "Processing"}</span>
        <div className="typing-dots" aria-hidden>
          <span /><span /><span />
        </div>
      </div>
    </div>
  );
}

function ClarificationBanner({ question }) {
  return (
    <div className="clarification-banner" role="status">
      <div className="clarification-banner-icon" aria-hidden>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <div>
        <div className="clarification-banner-label">Clarification needed</div>
        <p className="clarification-banner-text">{question}</p>
      </div>
    </div>
  );
}

function SendIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="15" height="15">
      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  );
}

export default function ChatWindow({
  messages,
  isLoading,
  currentAgent,
  waitingForClarification,
  clarificationQuestion,
  onSendMessage,
  onSendClarification,
}) {
  const [inputValue, setInputValue] = useState("");
  const [focused, setFocused] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const showWelcome = messages.length <= 1 && !isLoading;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = () => {
    if (!inputValue.trim() || isLoading) return;
    if (waitingForClarification) {
      onSendClarification(inputValue.trim());
    } else {
      onSendMessage(inputValue.trim());
    }
    setInputValue("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e) => {
    setInputValue(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 128)}px`;
  };

  const handleSuggestion = (text) => {
    if (isLoading) return;
    onSendMessage(text);
  };

  const canSend = !isLoading && inputValue.trim().length > 0;

  return (
    <div className="chat-window">
      <div className="chat-messages">
        {showWelcome && <WelcomeHero onSuggestion={handleSuggestion} />}

        {!showWelcome && messages.map((msg, i) => (
          <MessageBubble key={`${msg.role}-${i}`} message={msg} />
        ))}

        {isLoading && <TypingIndicator currentAgent={currentAgent} />}

        {waitingForClarification && (
          <ClarificationBanner question={clarificationQuestion} />
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <div className={`chat-input-box ${focused ? "chat-input-box--focused" : ""}`}>
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            value={inputValue}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            placeholder={
              waitingForClarification
                ? "Type your clarification..."
                : "Ask about any company — e.g. Tell me about Tesla's Q4 2025 results"
            }
            disabled={isLoading}
            rows={1}
            aria-label="Message input"
          />
          <button
            type="button"
            className={`btn-send ${canSend ? "btn-send--active" : "btn-send--disabled"}`}
            onClick={handleSend}
            disabled={!canSend}
            aria-label="Send message"
          >
            {isLoading ? <span className="btn-send-spinner" /> : <SendIcon />}
          </button>
        </div>
        <p className="chat-input-hint">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}



