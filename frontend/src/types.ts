export interface ChatResponse {
  session_id: string;
  reply: string;
  quick_replies: string[];
  state: string;
  intent?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  text: string;
}
