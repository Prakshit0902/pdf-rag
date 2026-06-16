"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import MarkdownRenderer from "./MarkdownRenderer";
import FileUpload from "./FileUpload";
import PdfViewerPanel, { type Citation } from "./PdfViewerPanel";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatSession {
  id: string;
  title: string;
  filename: string | null;
  created_at: string;
}

const getApiBaseUrl = () => {
  const nodeEnv = (
    process.env.NEXT_PUBLIC_NODE_ENV || 
    process.env.NODE_ENV || 
    "development"
  ).toLowerCase();

  if (nodeEnv === "production") {
    return (
      process.env.NEXT_PUBLIC_BASE_API_URL ||
      process.env.NEXT_BASE_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "https://pdf-rag-wjgd.onrender.com"
    );
  }
  return "http://localhost:8000";
};

const API_BASE = getApiBaseUrl();

export default function ChatInterface() {
  const { getToken, isLoaded, userId } = useAuth();

  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Automatically close active session if its related file was deleted
  useEffect(() => {
    if (currentSessionId && sessions.length > 0 && uploadedFiles.length > 0) {
      const activeSession = sessions.find((s) => s.id === currentSessionId);
      if (
        activeSession &&
        activeSession.filename &&
        !uploadedFiles.includes(activeSession.filename)
      ) {
        setCurrentSessionId(null);
        setMessages([]);
      }
    }
  }, [sessions, uploadedFiles, currentSessionId]);

  const hasLoadedInitialRef = useRef(false);
  const isSendingRef = useRef(false);

  // Fetch all sessions for the authenticated user
  const fetchSessions = useCallback(async () => {
    if (!userId) return;
    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/chat/sessions`, { headers });
      if (response.ok) {
        const data = await response.json();
        setSessions(data || []);
      }
    } catch (err) {
      console.error("Error fetching sessions:", err);
    }
  }, [userId, getToken]);

  // Load sessions on mount and auto-select the first one only once
  useEffect(() => {
    if (isLoaded && userId) {
      const loadInitialSessions = async () => {
        setIsLoadingSessions(true);
        try {
          const token = await getToken();
          const headers: Record<string, string> = {};
          if (token) {
            headers["Authorization"] = `Bearer ${token}`;
          }
          const response = await fetch(`${API_BASE}/chat/sessions`, { headers });
          if (response.ok) {
            const data = await response.json();
            setSessions(data || []);
            
            if (!hasLoadedInitialRef.current) {
              hasLoadedInitialRef.current = true;
              if (data && data.length > 0) {
                setCurrentSessionId(data[0].id);
              }
            }
          }
        } catch (err) {
          console.error("Error fetching initial sessions:", err);
        } finally {
          setIsLoadingSessions(false);
        }
      };
      loadInitialSessions();
    }
  }, [isLoaded, userId, getToken]);

  // Load messages whenever active session changes
  useEffect(() => {
    if (isSendingRef.current) return;

    if (isLoaded && userId && currentSessionId) {
      const fetchMessages = async () => {
        setIsLoadingMessages(true);
        try {
          const token = await getToken();
          const headers: Record<string, string> = {};
          if (token) {
            headers["Authorization"] = `Bearer ${token}`;
          }
          const response = await fetch(`${API_BASE}/chat/sessions/${currentSessionId}/messages`, { headers });
          if (response.ok) {
            const data = await response.json();
            setMessages(data.map((m: any) => ({
              role: m.role,
              content: m.content
            })));
          }
        } catch (err) {
          console.error("Error fetching messages:", err);
        } finally {
          setIsLoadingMessages(false);
        }
      };
      fetchMessages();
    } else if (!currentSessionId) {
      setMessages([]);
    }
  }, [currentSessionId, isLoaded, userId, getToken]);

  // Create a new session manually
  const handleCreateSession = async (title: string = "New Conversation", filename: string | null = null) => {
    if (isCreatingSession || !userId) return null;
    setIsCreatingSession(true);
    try {
      const token = await getToken();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/chat/sessions`, {
        method: "POST",
        headers,
        body: JSON.stringify({ title, filename }),
      });
      if (response.ok) {
        const data = await response.json();
        setSessions((prev) => [data, ...prev]);
        setCurrentSessionId(data.id);
        return data;
      }
    } catch (err) {
      console.error("Error creating session:", err);
    } finally {
      setIsCreatingSession(false);
    }
    return null;
  };

  const sendMessage = async (overrideQuestion?: string) => {
    const questionToSend = overrideQuestion || question;
    if (!questionToSend.trim() || isLoading || isStreaming) return;

    let sessionId = currentSessionId;
    if (!overrideQuestion) {
      setQuestion("");
    }
    setIsLoading(true);
    setIsStreaming(false);
    isSendingRef.current = true;

    try {
      const token = await getToken();
      
      // Auto-create session if none active
      if (!sessionId) {
        const title = questionToSend.slice(0, 30) + (questionToSend.length > 30 ? "..." : "");
        const primaryFile = selectedFiles.length > 0 ? selectedFiles[0] : null;
        const newSession = await handleCreateSession(title, primaryFile);
        if (!newSession) {
          throw new Error("Failed to create chat session");
        }
        sessionId = newSession.id;
      }

      // Add user message to state
      const userMessage: Message = { role: "user", content: questionToSend };
      setMessages((prev) => [...prev, userMessage]);

      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          question: questionToSend,
          session_id: sessionId,
          selected_files: selectedFiles,
        }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let assistantMessage = "";

      // Append blank message for assistant
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      let isFirstChunk = true;
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        if (isFirstChunk) {
          isFirstChunk = false;
          setIsLoading(false);
          setIsStreaming(true);
        }

        assistantMessage += decoder.decode(value, { stream: true });
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: "assistant", content: assistantMessage },
        ]);
      }
    } catch (err) {
      console.error("Error sending message:", err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Check connection to RAG server." },
      ]);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      isSendingRef.current = false;
      // Refresh sessions to pull updated title (if auto-created)
      fetchSessions();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleCitationClick = useCallback(
    (source: string, page: number, text: string) => {
      setActiveCitation({ source, page, text });
    },
    []
  );

  /** Open PDF viewer at page 1 when an indexed file is clicked from the sidebar */
  const handleFileClick = useCallback((filename: string) => {
    setActiveCitation({ source: filename, page: 1, text: "" });
  }, []);

  const getActiveSessionTitle = () => {
    const active = sessions.find((s) => s.id === currentSessionId);
    return active ? active.title : "New Conversation";
  };

  // Suggestions for empty state
  const suggestions = [
    "Summarize the document",
    "Explain key architectural findings",
    "What are the main limitations?",
    "List structural dependencies"
  ];

  return (
    <div className="w-full h-full flex flex-col md:flex-row overflow-hidden relative">

      {/* Mobile overlay backdrop when PDF viewer is open */}
      {activeCitation && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setActiveCitation(null)}
        />
      )}
      
      {/* Sidebar: Files & Conversations */}
      <div className="w-full md:w-80 bg-zinc-950/50 border-b md:border-b-0 md:border-r border-zinc-900 flex flex-col flex-shrink-0 h-80 md:h-full">
        {/* Upload box & indexed files */}
        <div className="p-4 border-b border-zinc-900 flex-shrink-0">
          <FileUpload
            mode="sidebar"
            uploadedFiles={uploadedFiles}
            setUploadedFiles={setUploadedFiles}
            selectedFiles={selectedFiles}
            setSelectedFiles={setSelectedFiles}
            onFileClick={handleFileClick}
          />
        </div>

        {/* Conversation Sessions List */}
        <div className="flex-1 flex flex-col min-h-0">
          <div className="p-4 flex items-center justify-between flex-shrink-0">
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Conversations</span>
            <button
              onClick={() => handleCreateSession("New Conversation", selectedFiles.length > 0 ? selectedFiles[0] : null)}
              disabled={isCreatingSession}
              className="w-6 h-6 rounded bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white flex items-center justify-center border border-zinc-800/80 transition-all cursor-pointer"
              title="New Chat"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>

          {/* Sessions list */}
          <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1.5 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
            {isLoadingSessions && sessions.length === 0 ? (
              <div className="text-center text-xs text-zinc-600 py-4">Loading sessions...</div>
            ) : sessions.length === 0 ? (
              <div className="text-center text-xs text-zinc-600 py-4 italic">No chats started yet</div>
            ) : (
              sessions.map((sess) => (
                <button
                  key={sess.id}
                  onClick={() => setCurrentSessionId(sess.id)}
                  className={`w-full text-left p-2.5 rounded-xl text-xs flex items-center gap-2.5 transition-all truncate border group cursor-pointer ${
                    currentSessionId === sess.id
                      ? "bg-indigo-950/20 text-indigo-300 border-indigo-500/20 font-medium"
                      : "bg-transparent text-zinc-400 border-transparent hover:bg-zinc-900/40 hover:text-zinc-200"
                  }`}
                >
                  <svg className="w-3.5 h-3.5 text-zinc-500 group-hover:text-zinc-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <span className="truncate flex-1">{sess.title}</span>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Workspace Isolation Status */}
        <div className="p-4 border-t border-zinc-900 bg-zinc-950/25 flex-shrink-0">
          <div className="text-[10px] text-zinc-500 leading-relaxed">
            <span className="font-semibold text-zinc-400 block mb-0.5 uppercase tracking-wide">Workspace Isolation</span>
            All caches, vector chunks, index catalogs, and message histories are fully partitioned by your Clerk Tenant ID.
          </div>
        </div>
      </div>

      {/* Main Chat Panel */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-zinc-900/5">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-zinc-900 flex items-center justify-between flex-shrink-0">
          <div>
            <h3 className="text-sm font-semibold text-zinc-200 truncate max-w-md">{getActiveSessionTitle()}</h3>
            <p className="text-[9px] text-zinc-500 font-medium uppercase mt-0.5 tracking-wider">Tenant Session</p>
          </div>
          {currentSessionId && (
            <button
              onClick={() => {
                setCurrentSessionId(null);
                setMessages([]);
              }}
              className="text-[10px] px-2.5 py-1 rounded-lg bg-zinc-950/50 border border-zinc-900 text-zinc-400 hover:text-zinc-200 hover:border-zinc-800 transition-all cursor-pointer"
            >
              Close Session
            </button>
          )}
        </div>

        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          {isLoadingMessages ? (
            <div className="h-full flex items-center justify-center flex-col gap-2">
              <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-zinc-500">Loading conversation history...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center text-center px-4 max-w-md mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-zinc-950 flex items-center justify-center border border-zinc-900 mb-4 text-indigo-400 shadow-inner">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h4 className="text-sm font-semibold text-zinc-300">How can I assist with your documents?</h4>
              <p className="text-xs text-zinc-500 mt-1 mb-6 leading-relaxed">
                Submit a question below to query the selected files in your tenant-isolated vector store.
              </p>
              
              {/* Suggestion Chips */}
              <div className="grid grid-cols-2 gap-2.5 w-full">
                {suggestions.map((sug, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(sug)}
                    disabled={isLoading || isStreaming}
                    className="p-3 text-[11px] bg-zinc-950/40 hover:bg-zinc-950/80 border border-zinc-900 hover:border-zinc-800 text-zinc-400 hover:text-zinc-200 rounded-xl transition-all text-left font-medium leading-tight cursor-pointer"
                  >
                    {sug}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-2xl max-w-[85%] ${
                    msg.role === "user"
                      ? "bg-indigo-600/90 text-white self-end ml-12 rounded-tr-none shadow-[0_4px_12px_rgba(99,102,241,0.25)] border border-indigo-500/20"
                      : "bg-zinc-900/80 text-zinc-100 self-start mr-12 rounded-tl-none border border-zinc-800/80 shadow-md"
                  }`}
                >
                  {msg.role === "user" ? (
                    <p className="text-xs whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  ) : (
                    <div className="relative">
                      <MarkdownRenderer
                        content={msg.content}
                        isStreaming={isStreaming && i === messages.length - 1}
                        onCitationClick={handleCitationClick}
                      />
                      {isLoading && i === messages.length - 1 && msg.content === "" && (
                        <div className="flex gap-1 items-center py-1 mt-2">
                          <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Form */}
        <div className="p-4 border-t border-zinc-900 flex-shrink-0">
          <div className="flex gap-2 max-w-4xl mx-auto w-full">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your PDF..."
              className="flex-1 px-4 py-3 bg-zinc-950/50 border border-zinc-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500 text-sm text-zinc-200 placeholder-zinc-500 transition-all"
              disabled={isLoading || isStreaming || isLoadingMessages}
            />
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || isStreaming || isLoadingMessages || !question.trim()}
              className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-zinc-800 text-white rounded-xl font-medium shadow-[0_0_15px_rgba(99,102,241,0.2)] disabled:shadow-none hover:shadow-[0_0_20px_rgba(99,102,241,0.35)] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center cursor-pointer"
            >
              {isLoading || isStreaming ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── PDF Viewer Panel ──────────────────────────────────── */}
      {/* On desktop: right-side panel that expands inline.       */}
      {/* On mobile:  fixed overlay panel over the full screen.   */}
      <div
        className={`
          md:relative md:flex md:h-full transition-all duration-300
          ${
            activeCitation
              ? "fixed inset-y-0 right-0 z-50 w-full md:w-auto md:static md:z-auto"
              : "hidden md:flex md:w-0"
          }
        `}
      >
        <PdfViewerPanel
          citation={activeCitation}
          onClose={() => setActiveCitation(null)}
        />
      </div>

    </div>
  );
}