"use client";

import { useState } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    const question = input.trim();
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
    <div className="flex min-h-screen flex-col items-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-2xl flex-1 flex-col py-8 px-4">
        <h1 className="mb-4 text-xl font-semibold text-black dark:text-zinc-50">
          Data Analysis Agent
        </h1>

        <div className="flex flex-1 flex-col gap-3 overflow-y-auto rounded-lg border border-black/[.08] bg-white p-4 dark:border-white/[.145] dark:bg-zinc-900">
          {messages.length === 0 && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              데이터에 대해 질문해보세요.
            </p>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={
                m.role === "user"
                  ? "self-end rounded-lg bg-blue-600 px-3 py-2 text-sm text-white max-w-[80%]"
                  : "self-start rounded-lg bg-zinc-100 px-3 py-2 text-sm text-black max-w-[80%] dark:bg-zinc-800 dark:text-zinc-50 whitespace-pre-wrap"
              }
            >
              {m.content}
            </div>
          ))}
          {loading && (
            <div className="self-start rounded-lg bg-zinc-100 px-3 py-2 text-sm text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400">
              분석 중...
            </div>
          )}
        </div>

        <div className="mt-4 flex gap-2">
          <input
            className="flex-1 rounded-lg border border-black/[.08] bg-white px-3 py-2 text-sm text-black outline-none dark:border-white/[.145] dark:bg-zinc-900 dark:text-zinc-50"
            placeholder="질문을 입력하세요..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
            disabled={loading}
          />
          <button
            className="rounded-lg bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-50"
            onClick={sendMessage}
            disabled={loading}
          >
            전송
          </button>
        </div>
      </main>
    </div>
  );
}
