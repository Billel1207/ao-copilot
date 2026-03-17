"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Loader2, MessageSquare, BookOpen, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import { apiClient } from "@/lib/api";

interface Props {
  projectId: string;
}

interface Citation {
  doc_name: string;
  page_start: number;
  page_end: number;
  doc_type: string;
  snippet: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timestamp: Date;
  streaming?: boolean;
}

const SUGGESTED_QUESTIONS = [
  "Quelle est la date limite de remise des offres ?",
  "Quels documents administratifs sont requis ?",
  "Quel est le budget estimé du marché ?",
  "Y a-t-il une visite de site obligatoire ?",
];

// ── Message bubble ───────────────────────────────────────────────────────────
function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3 animate-slide-up", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      <div className={cn(
        "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold mt-0.5",
        isUser
          ? "bg-primary-700 text-white"
          : "bg-gradient-to-br from-primary-500 to-primary-700 text-white"
      )}>
        {isUser ? "V" : <Sparkles className="w-3.5 h-3.5" />}
      </div>

      <div className={cn("flex flex-col gap-1 max-w-[85%]", isUser ? "items-end" : "items-start")}>
        {/* Bubble */}
        <div className={cn(
          "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-primary-700 text-white rounded-tr-sm"
            : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm prose prose-sm prose-slate max-w-none"
        )}>
          {isUser ? message.content : (
            <>
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-0.5">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>,
                  li: ({ children }) => <li className="text-sm">{children}</li>,
                  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                  h3: ({ children }) => <h3 className="font-semibold text-sm mt-2 mb-1">{children}</h3>,
                  code: ({ children }) => <code className="bg-slate-100 px-1 rounded text-xs font-mono">{children}</code>,
                }}
              >
                {message.content}
              </ReactMarkdown>
              {message.streaming && <span className="animate-pulse">▌</span>}
            </>
          )}
        </div>

        {/* Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-1">
            {message.citations.map((cit, i) => (
              <div
                key={i}
                className="group relative inline-flex items-center gap-1 text-[10px] font-medium
                           bg-primary-50 text-primary-700 border border-primary-100 rounded-full px-2 py-0.5 cursor-help"
                title={cit.snippet}
              >
                <BookOpen className="w-2.5 h-2.5" />
                {cit.doc_name} p.{cit.page_start}

                {/* Tooltip snippet */}
                <div className="absolute bottom-full left-0 mb-2 hidden group-hover:block
                                w-56 bg-slate-900 text-white text-[10px] rounded-lg p-2.5 z-10 shadow-xl leading-relaxed">
                  {cit.snippet}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className="text-[10px] text-slate-300">
          {message.timestamp.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  );
}

// ── Typing indicator ─────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex gap-3 animate-fade-in">
      <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0
                      bg-gradient-to-br from-primary-500 to-primary-700 text-white">
        <Sparkles className="w-3.5 h-3.5" />
      </div>
      <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-sm px-4 py-2.5 shadow-sm">
        <div className="flex items-center gap-1">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-slate-400"
              style={{
                animation: `bounce 1s ease-in-out ${i * 0.15}s infinite`,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Main Component ───────────────────────────────────────────────────────────
export function ChatTab({ projectId }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Bonjour ! Je suis votre assistant DCE. Posez-moi n'importe quelle question sur ce dossier d'appel d'offres — je réponds en me basant uniquement sur vos documents.",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const sendMessage = async (question?: string) => {
    const q = (question ?? input).trim();
    if (!q || isSending) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: q,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    const assistantMsgId = (Date.now() + 1).toString();

    try {
      const response = await apiClient.post(
        `/api/v1/projects/${projectId}/chat/stream`,
        { question: q }
      );

      if (!response.ok) throw new Error("Erreur serveur");
      if (!response.body) throw new Error("Pas de streaming");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      // Ajouter le message assistant vide avec indicateur de streaming
      setMessages((prev) => [
        ...prev,
        { id: assistantMsgId, role: "assistant", content: "", streaming: true, citations: [], timestamp: new Date() },
      ]);

      let done = false;
      while (!done) {
        const { done: streamDone, value } = await reader.read();
        done = streamDone;
        if (!value) continue;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const data = line.slice(6);
          if (data === "[DONE]") {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId ? { ...m, streaming: false } : m
              )
            );
            done = true;
            break;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.type === "token") {
              accumulatedText += parsed.text;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, content: accumulatedText } : m
                )
              );
            } else if (parsed.type === "citations") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId ? { ...m, citations: parsed.citations } : m
                )
              );
            } else if (parsed.type === "error") {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: `Désolé, une erreur est survenue : ${parsed.message}`, streaming: false }
                    : m
                )
              );
              done = true;
              break;
            }
          } catch {
            // ligne SSE non-JSON — ignorer
          }
        }
      }
    } catch {
      setMessages((prev) => {
        const existing = prev.find((m) => m.id === assistantMsgId);
        if (existing) {
          return prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: "Désolé, une erreur est survenue. Veuillez réessayer.", streaming: false }
              : m
          );
        }
        return [
          ...prev,
          {
            id: assistantMsgId,
            role: "assistant" as const,
            content: "Désolé, une erreur est survenue. Veuillez réessayer.",
            timestamp: new Date(),
          },
        ];
      });
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-280px)] min-h-[400px]">

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50 rounded-xl border border-slate-100">

        {messages.length === 1 && (
          /* Suggested questions */
          <div className="mt-2">
            <p className="text-xs text-slate-400 font-medium mb-2 flex items-center gap-1.5">
              <MessageSquare className="w-3 h-3" /> Questions suggérées
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="text-left text-xs bg-white border border-slate-200 rounded-xl px-3 py-2.5
                             text-slate-600 hover:border-primary-300 hover:text-primary-700 hover:bg-primary-50
                             transition-all duration-150 shadow-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isSending && !messages.some((m) => m.streaming) && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="pt-3">
        <div className="flex items-end gap-2 bg-white border border-slate-200 rounded-xl p-2 shadow-sm
                        focus-within:border-primary-400 focus-within:ring-2 focus-within:ring-primary-100 transition-all">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Posez une question sur le DCE… (Entrée pour envoyer)"
            rows={1}
            className="flex-1 resize-none text-sm text-slate-800 placeholder:text-slate-400 bg-transparent
                       outline-none py-1.5 px-2 max-h-28 overflow-y-auto"
            style={{ lineHeight: "1.5" }}
            disabled={isSending}
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isSending}
            className={cn(
              "flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center transition-all",
              input.trim() && !isSending
                ? "bg-primary-700 text-white hover:bg-primary-800 shadow-sm"
                : "bg-slate-100 text-slate-300 cursor-not-allowed"
            )}
          >
            {isSending
              ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
              : <Send className="w-3.5 h-3.5" />
            }
          </button>
        </div>
        <p className="text-[10px] text-slate-300 mt-1.5 text-center">
          Réponses basées uniquement sur vos documents • 20 questions/heure
        </p>
      </div>

      {/* Keyframe animation for dots */}
      <style jsx>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-3px); }
        }
      `}</style>
    </div>
  );
}
