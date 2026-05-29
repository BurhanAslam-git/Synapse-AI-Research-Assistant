const STORAGE_KEY = "synapse_chat_history";
const MAX_CONVERSATIONS = 50;

export const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Hello! I'm your Synapse AI Research Assistant. Ask me about any company — I'll research it using specialized AI agents.",
};

export const NEW_CHAT_MESSAGE = {
  role: "assistant",
  content: "New conversation started. Ask me about any company.",
};

export function getDefaultMessages() {
  return [WELCOME_MESSAGE];
}

export function hasUserMessages(messages) {
  return messages.some((m) => m.role === "user");
}

export function deriveTitle(messages) {
  const firstUser = messages.find((m) => m.role === "user");
  if (!firstUser?.content) return "Untitled chat";
  const text = firstUser.content.trim().replace(/\s+/g, " ");
  if (text.length <= 44) return text;
  return `${text.slice(0, 44)}…`;
}

export function loadConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((c) => c?.id && Array.isArray(c.messages))
      .sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
  } catch {
    return [];
  }
}

export function saveConversations(conversations) {
  try {
    const trimmed = conversations.slice(0, MAX_CONVERSATIONS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    return trimmed;
  } catch {
    return conversations;
  }
}

export function upsertConversation(conversations, entry) {
  const without = conversations.filter((c) => c.id !== entry.id);
  const next = [entry, ...without].sort(
    (a, b) => (b.updatedAt || 0) - (a.updatedAt || 0)
  );
  return saveConversations(next);
}

export function removeConversation(conversations, id) {
  return saveConversations(conversations.filter((c) => c.id !== id));
}

export function formatRelativeTime(timestamp) {
  if (!timestamp) return "";
  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  return new Date(timestamp).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function buildConversationEntry({ threadId, messages, createdAt }) {
  const now = Date.now();
  return {
    id: threadId,
    threadId,
    title: deriveTitle(messages),
    messages,
    createdAt: createdAt || now,
    updatedAt: now,
  };
}
