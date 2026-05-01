import React, { useState, useRef, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || 'mkt-key-2026';
const VISIT_ID = 541;

interface Message {
  id: string;
  from: 'user' | 'bot';
  text: string;
}

interface Props {
  role?: string;
}

export default function ChatWidget({ role = 'marketing' }: Props) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      from: 'bot',
      text: '👋 Bonjour ! Je suis votre assistant IA.\nPosez-moi des questions sur vos prédictions, CA, délégués ou zones géographiques.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: Date.now().toString(), from: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({ message: text, role, visit_id: VISIT_ID }),
      });
      const json = await res.json();
      setMessages(prev => [
        ...prev,
        { id: Date.now().toString() + 'b', from: 'bot', text: json.reply || '🤖 Réponse non disponible.' },
      ]);
    } catch {
      setMessages(prev => [
        ...prev,
        { id: Date.now().toString() + 'e', from: 'bot', text: '⚠️ Serveur non disponible.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {/* Chat panel */}
      {open && (
        <div className="w-[360px] h-[500px] bg-[#18181C] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10 bg-[#0E0E10]">
            <div>
              <p className="text-white font-semibold text-sm">🤖 Assistant IA</p>
              <p className="text-[#2DD4BF] text-xs mt-0.5">Orchestrateur · {role}</p>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-400 hover:text-white text-lg leading-none"
            >✕</button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-3">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`max-w-[85%] px-3 py-2 rounded-xl text-sm whitespace-pre-wrap leading-relaxed ${
                  msg.from === 'user'
                    ? 'self-end bg-[#2DD4BF] text-[#0E0E10] font-medium'
                    : 'self-start bg-[#22222A] border border-white/8 text-gray-200'
                }`}
              >
                {msg.text}
              </div>
            ))}
            {loading && (
              <div className="self-start bg-[#22222A] border border-white/8 text-gray-400 text-xs px-3 py-2 rounded-xl">
                ⏳ Analyse en cours...
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="flex items-center gap-2 px-3 py-3 border-t border-white/10 bg-[#0E0E10]">
            <input
              className="flex-1 bg-[#22222A] border border-white/10 rounded-full px-4 py-2 text-sm text-white placeholder-gray-500 outline-none focus:border-[#2DD4BF]/40"
              placeholder="Posez votre question..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="w-9 h-9 rounded-full bg-[#2DD4BF] flex items-center justify-center text-[#0E0E10] disabled:opacity-40 hover:bg-[#2DD4BF]/80 transition-colors"
            >
              ➤
            </button>
          </div>
        </div>
      )}

      {/* FAB */}
      <button
        onClick={() => setOpen(o => !o)}
        className="w-14 h-14 rounded-full bg-[#2DD4BF] text-[#0E0E10] text-2xl shadow-lg hover:bg-[#2DD4BF]/80 transition-all hover:scale-105 flex items-center justify-center"
        title="Assistant IA"
      >
        {open ? '✕' : '💬'}
      </button>
    </div>
  );
}
