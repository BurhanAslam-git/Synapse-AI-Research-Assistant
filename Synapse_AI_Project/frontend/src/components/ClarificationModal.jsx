import { useState } from "react";

export default function ClarificationModal({ question, onSubmit }) {
  const [answer, setAnswer] = useState("");

  const handleSubmit = () => {
    if (!answer.trim()) return;
    onSubmit(answer.trim());
    setAnswer("");
  };

  const canSubmit = answer.trim().length > 0;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="clarify-title">
      <div className="modal-card">
        <div className="modal-icon" aria-hidden>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        </div>

        <h2 id="clarify-title" className="modal-title">Clarification needed</h2>
        <p className="modal-question">{question}</p>

        <div className="modal-divider" />

        <textarea
          className="modal-textarea"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSubmit();
            }
          }}
          placeholder="Type your clarification here..."
          autoFocus
          rows={3}
          aria-label="Clarification answer"
        />

        <button
          type="button"
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!canSubmit}
          style={!canSubmit ? { opacity: 0.5, cursor: "not-allowed", transform: "none" } : undefined}
        >
          Submit clarification
        </button>

        <p className="modal-hint">Press Enter to submit</p>
      </div>
    </div>
  );
}


