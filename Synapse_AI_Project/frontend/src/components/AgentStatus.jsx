const AGENTS = [
  {
    key: "Clarity Agent",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
      </svg>
    ),
  },
  {
    key: "Research Agent",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
    ),
  },
  {
    key: "Validator Agent",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    ),
  },
  {
    key: "Synthesis Agent",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>
      </svg>
    ),
  },
];

function AgentCard({ agent, completed, running }) {
  const stateClass = running
    ? "agent-card--running"
    : completed
    ? "agent-card--complete"
    : "";

  const statusLabel = running ? "Running" : completed ? "Complete" : "Waiting";

  return (
    <div className={`agent-card ${stateClass}`}>
      <span className="agent-card-dot" aria-hidden />
      <div className="agent-card-icon">{agent.icon}</div>
      <div>
        <div className="agent-card-name">{agent.key}</div>
        <div className="agent-card-status">{statusLabel}</div>
      </div>
    </div>
  );
}

export default function AgentStatus({ steps, currentAgent, isLoading }) {
  return (
    <aside className="agent-panel" aria-label="Pipeline status">
      <header className="agent-panel-header">
        <div>
          <div className="agent-panel-title">Pipeline Status</div>
          <p className="agent-panel-sub">Live agent progress</p>
        </div>
      </header>

      <div className="agent-cards">
        {AGENTS.map((agent) => {
          const completed = steps.some((s) => s.includes(agent.key));
          const running = currentAgent === agent.key && isLoading;
          return (
            <AgentCard
              key={agent.key}
              agent={agent}
              completed={completed}
              running={running}
            />
          );
        })}
      </div>

      {steps.length > 0 && (
        <div className="agent-step-log">
          <div className="agent-step-log-divider" />
          <div className="agent-step-log-label">Step log</div>
          {steps.map((step, i) => (
            <div key={`${step}-${i}`} className="agent-step-item">
              {step}
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}


