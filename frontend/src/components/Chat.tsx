import { useEffect, useRef, useState, type FormEvent } from "react";
import { fetchWelcome, resetSession, sendMessage } from "../api";
import type { ChatMessage } from "../types";

function createMessage(role: ChatMessage["role"], text: string): ChatMessage {
  return {
    id: `${role}-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    role,
    text,
  };
}

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [quickReplies, setQuickReplies] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const initialized = useRef(false);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (initialized.current) {
      return;
    }
    initialized.current = true;
    void loadWelcome();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function loadWelcome() {
    setError(null);
    setLoading(true);
    try {
      const data = await fetchWelcome();
      setMessages([createMessage("bot", data.reply)]);
      setQuickReplies(data.quick_replies ?? []);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось загрузить приветствие");
    } finally {
      setLoading(false);
    }
  }

  async function submit(text: string) {
    const value = text.trim();
    if (!value) {
      return;
    }
    setError(null);
    setLoading(true);
    setMessages((current) => [...current, createMessage("user", value)]);
    try {
      const data = await sendMessage(value);
      setMessages((current) => [...current, createMessage("bot", data.reply)]);
      setQuickReplies(data.quick_replies ?? []);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Не удалось отправить сообщение");
    } finally {
      setLoading(false);
    }
  }

  function handleFormSubmit(event: FormEvent) {
    event.preventDefault();
    const value = input;
    setInput("");
    void submit(value);
  }

  async function handleReset() {
    await resetSession();
    setMessages([]);
    setQuickReplies([]);
    setError(null);
    void loadWelcome();
  }

  return (
    <section className="chat">
      <div className="chat-toolbar">
        <span className="chat-status">
          <span className="dot" /> Бот онлайн
        </span>
        <button type="button" className="reset-button" onClick={handleReset}>
          Начать заново
        </button>
      </div>

      <div className="chat-body">
        {messages.map((message) => (
          <div key={message.id} className={`bubble ${message.role}`}>
            {message.text}
          </div>
        ))}
        {loading && <div className="bubble bot typing">Печатает…</div>}
        {error && <div className="bubble error">{error}</div>}
        <div ref={bottomRef} />
      </div>

      {quickReplies.length > 0 && (
        <div className="quick-replies">
          {quickReplies.map((reply) => (
            <button
              key={reply}
              type="button"
              className="chip"
              disabled={loading}
              onClick={() => void submit(reply)}
            >
              {reply}
            </button>
          ))}
        </div>
      )}

      <form className="chat-input" onSubmit={handleFormSubmit}>
        <input
          type="text"
          value={input}
          placeholder="Напишите вопрос…"
          onChange={(event) => setInput(event.target.value)}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Отправить
        </button>
      </form>
    </section>
  );
}
