import type { ChatResponse } from "./types";

const SESSION_KEY = "synergy-chat-session";

function createId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `s-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = createId();
    localStorage.setItem(SESSION_KEY, sessionId);
  }
  return sessionId;
}

export function setSessionId(sessionId: string): void {
  localStorage.setItem(SESSION_KEY, sessionId);
}

export async function sendMessage(message: string): Promise<ChatResponse> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: getSessionId(), message }),
  });
  if (!response.ok) {
    throw new Error(`Сервер вернул ошибку ${response.status}`);
  }
  const data = (await response.json()) as ChatResponse;
  setSessionId(data.session_id);
  return data;
}

export async function resetSession(): Promise<void> {
  await fetch("/api/session/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: getSessionId() }),
  });
}
