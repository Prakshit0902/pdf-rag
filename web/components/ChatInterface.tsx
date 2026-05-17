"use client";

import { useState, useRef, useEffect } from "react";
import MarkdownRenderer from "./MarkdownRenderer";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatInterface() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!question.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let assistantMessage = "";

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        assistantMessage += decoder.decode(value, { stream: true });
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: "assistant", content: assistantMessage },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="w-full max-w-md p-6 bg-white rounded-lg shadow-md border border-zinc-200">
      <h2 className="text-xl font-semibold mb-4 text-zinc-800">Chat</h2>

      <div className="h-80 overflow-y-auto space-y-4 mb-4 p-2 border border-zinc-100 rounded-lg bg-zinc-50">
        {messages.length === 0 ? (
          <p className="text-zinc-400 text-center text-sm">Ask a question about your PDF</p>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg ${
                msg.role === "user"
                  ? "bg-zinc-900 text-white ml-8"
                  : "bg-white text-zinc-800 mr-8 border border-zinc-200"
              }`}
            >
              {msg.role === "user" ? (
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              ) : (
                <div className="relative">
                  <MarkdownRenderer content={msg.content} />
                  {isLoading && i === messages.length - 1 && (
                    <span className="inline-block w-2 h-4 bg-zinc-400 ml-0.5 animate-pulse" />
                  )}
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          className="flex-1 px-4 py-2 border border-zinc-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-zinc-900 text-zinc-800"
          disabled={isLoading}
        />
        <button
          onClick={sendMessage}
          disabled={isLoading || !question.trim()}
          className="px-4 py-2 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}