import { formatRelativeTime } from "../utils/chatHistory";

const AGENTS = [
  {
    name: "Clarity Agent",
    desc: "Evaluates query precision",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
    ),
  },
  {
    name: "Research Agent",
    desc: "Fetches live company data",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
    ),
  },
  {
    name: "Validator Agent",
    desc: "Assesses data quality",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    ),
  },
  {
    name: "Synthesis Agent",
    desc: "Composes final report",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
    ),
  },
];

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="12" height="12">
      <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    </svg>
  );
}

function formatChatMeta(chat) {
  const count = chat.messages?.filter((m) => m.role === "user").length || 0;
  const time = formatRelativeTime(chat.updatedAt);
  const turns = count === 1 ? "1 message" : `${count} messages`;
  return `${turns} · ${time}`;
}

export default function Sidebar({
  conversations,
  activeThreadId,
  activeTitle,
  onSelectConversation,
  onDeleteConversation,
  onReset,
  isLoading,
}) {
  const pastChats = conversations.filter((c) => c.threadId !== activeThreadId);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-row">
          <div className="sidebar-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>
          <div>
            <div className="sidebar-title">Synapse AI</div>
            <div className="sidebar-subtitle">Research Assistant</div>
          </div>
        </div>
      </div>

      <div className="sidebar-divider" />

      <div className="sidebar-actions">
        <button type="button" className="btn-primary" onClick={onReset} disabled={isLoading}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" width="13" height="13">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          <span>New Conversation</span>
        </button>
      </div>

      <div className="sidebar-history">
        <div className="sidebar-section-label">Chat history</div>
        <div className="history-list" role="list">
          <div className="history-item history-item--active" role="listitem" aria-current="true">
            <span className="history-item-icon" aria-hidden><ChatIcon /></span>
            <span className="history-item-body">
              <span className="history-item-title">{activeTitle}</span>
              <span className="history-item-meta">Active now</span>
            </span>
          </div>

          {pastChats.length === 0 && (
            <p className="history-empty">Past chats appear here when you start a new conversation.</p>
          )}

          {pastChats.map((chat) => (
            <div key={chat.id} className="history-item-wrap" role="listitem">
              <button
                type="button"
                className="history-item"
                onClick={() => onSelectConversation(chat)}
                disabled={isLoading}
              >
                <span className="history-item-icon" aria-hidden><ChatIcon /></span>
                <span className="history-item-body">
                  <span className="history-item-title">{chat.title}</span>
                  <span className="history-item-meta">{formatChatMeta(chat)}</span>
                </span>
              </button>
              <button
                type="button"
                className="history-item-delete"
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteConversation(chat.id);
                }}
                aria-label={`Delete chat: ${chat.title}`}
                title="Delete chat"
              >
                <TrashIcon />
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="sidebar-divider sidebar-divider--inset" />

      <div className="sidebar-pipeline">
        <div className="sidebar-section-label">Agent pipeline</div>
        <div className="pipeline-list">
          {AGENTS.map((agent, i) => (
            <div key={agent.name} className="pipeline-item">
              {i < AGENTS.length - 1 && <div className="pipeline-connector" aria-hidden />}
              <div className="pipeline-icon">{agent.icon}</div>
              <div>
                <div className="pipeline-name">{agent.name}</div>
                <div className="pipeline-desc">{agent.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <footer className="sidebar-footer">
        <div className="sidebar-footer-dot" aria-hidden />
        <span>LangGraph · FastAPI · GPT-4</span>
      </footer>
    </aside>
  );
}
