"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

const SUGGESTIONS = [
  "현재 가장 최근 데이터는 뭐야?",
  "BTC 평균, 최고, 최저 가격 알려줘",
  "ETH 최근 가격 추이 보여줘",
];

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage(text?: string) {
    const question = (text ?? input).trim();
    if (!question || loading) return;

    const nextMessages: ChatMessage[] = [
      ...messages,
      { role: "user", content: question },
    ];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });

      if (!res.ok) {
        throw new Error(`request failed: ${res.status}`);
      }

      const data = (await res.json()) as { reply: string };
      setMessages([
        ...nextMessages,
        { role: "assistant", content: data.reply },
      ]);
    } catch {
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: "요청 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-[#0a0e14] font-sans">
      <main className="flex w-full max-w-2xl flex-1 flex-col px-4 py-8">
        <header className="mb-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-emerald-400 text-lg font-bold text-black">
            ₿
          </div>
          <div>
            <h1 className="text-lg font-semibold text-zinc-50">
              Crypto Data Analysis Agent
            </h1>
            <p className="text-xs text-zinc-500">BTC · ETH 실시간 수집 데이터 기반 분석</p>
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-2xl border border-zinc-800 bg-[#0f1420] p-4">
          {messages.length === 0 && (
            <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
              <p className="text-sm text-zinc-500">
                BTC/ETH 가격 데이터에 대해 질문해보세요.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="rounded-full border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 transition-colors hover:border-emerald-500 hover:text-emerald-400"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user"
                  ? "self-end max-w-[85%] rounded-2xl rounded-br-sm bg-emerald-600 px-3.5 py-2 text-sm text-white"
                  : "self-start max-w-[90%] rounded-2xl rounded-bl-sm border border-zinc-800 bg-[#161c29] px-3.5 py-2.5 text-sm text-zinc-100"
              }
            >
              {m.role === "assistant" ? (
                <div className="markdown-body">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {m.content}
                  </ReactMarkdown>
                </div>
              ) : (
                m.content
              )}
            </div>
          ))}
          {loading && (
            <div className="self-start rounded-2xl rounded-bl-sm border border-zinc-800 bg-[#161c29] px-3.5 py-2 text-sm text-zinc-500">
              데이터 조회 및 분석 중...
            </div>
          )}
        </div>

        <div className="mt-4 flex gap-2">
          <input
            className="flex-1 rounded-xl border border-zinc-800 bg-[#0f1420] px-3.5 py-2.5 text-sm text-zinc-50 outline-none placeholder:text-zinc-600 focus:border-emerald-500"
            placeholder="예: BTC 최근 7일 가격 알려줘"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
            disabled={loading}
          />
          <button
            className="rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-medium text-black transition-colors hover:bg-emerald-400 disabled:opacity-40"
            onClick={() => sendMessage()}
            disabled={loading}
          >
            전송
          </button>
        </div>
      </main>
    </div>
  );
}
