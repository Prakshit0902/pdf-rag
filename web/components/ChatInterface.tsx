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
  ).toLowerCase().replace(/"/g, "");

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

  // Layout state for the restructured, decluttered workspace shell
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSourcesOpen, setIsSourcesOpen] = useState(false);

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

  const selectedCount = selectedFiles.length;
  const indexedCount = uploadedFiles.length;

  return (
    <div className="w-full h-full flex overflow-hidden relative bg-background">

      {/* ── Mobile backdrop for the conversations rail ───────────── */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* ── Conversations rail (dedicated, collapsible) ──────────── */}
      <aside
        className={`
          z-40 flex h-full flex-col flex-shrink-0 overflow-hidden
          border-r border-border-subtle bg-surface/60 backdrop-blur-sm
          transition-[width,transform] duration-300 ease-in-out
          fixed inset-y-0 left-0 w-72 md:static md:inset-auto
          ${isSidebarOpen ? "translate-x-0 md:w-72" : "-translate-x-full md:translate-x-0 md:w-0 md:border-r-0"}
        `}
      >
        <div className="flex h-full w-72 flex-col">
          {/* New chat */}
          <div className="p-3 flex-shrink-0">
            <button
              onClick={() => {
                handleCreateSession("New Conversation", selectedFiles.length > 0 ? selectedFiles[0] : null);
                setIsSidebarOpen((o) => (window.innerWidth < 768 ? false : o));
              }}
              disabled={isCreatingSession}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-foreground px-4 py-2.5 text-sm font-semibold text-background shadow-sm transition-all hover:opacity-90 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New chat
            </button>
          </div>

          {/* Sessions list */}
          <div className="flex-1 flex flex-col min-h-0">
            <div className="px-4 pt-2 pb-1 flex-shrink-0">
              <span className="text-[10px] font-bold text-muted uppercase tracking-wider">Recent</span>
            </div>
            <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-1">
              {isLoadingSessions && sessions.length === 0 ? (
                <div className="text-center text-xs text-muted py-4">Loading sessions...</div>
              ) : sessions.length === 0 ? (
                <div className="text-center text-xs text-muted/70 py-6 italic px-4">No conversations yet. Start one above.</div>
              ) : (
                sessions.map((sess) => (
                  <button
                    key={sess.id}
                    onClick={() => {
                      setCurrentSessionId(sess.id);
                      if (window.innerWidth < 768) setIsSidebarOpen(false);
                    }}
                    className={`w-full text-left p-2.5 rounded-xl text-xs flex items-center gap-2.5 transition-all truncate border group cursor-pointer ${
                      currentSessionId === sess.id
                        ? "bg-accent-soft text-accent border-accent/30 font-medium"
                        : "bg-transparent text-muted border-transparent hover:bg-surface-2 hover:text-foreground"
                    }`}
                  >
                    <svg className={`w-3.5 h-3.5 flex-shrink-0 ${currentSessionId === sess.id ? "text-accent" : "text-muted/70 group-hover:text-muted"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <span className="truncate flex-1">{sess.title}</span>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Tenant isolation badge */}
          <div className="p-3 border-t border-border-subtle flex-shrink-0">
            <div className="flex items-center gap-2.5 rounded-xl bg-surface-2/50 border border-border-subtle px-3 py-2.5">
              <svg className="w-4 h-4 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <div className="min-w-0">
                <p className="text-[11px] font-semibold text-foreground leading-tight">Tenant-isolated</p>
                <p className="text-[10px] text-muted leading-tight">Indexes & history are private to you.</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main Chat Column ─────────────────────────────────────── */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-background min-w-0">

        {/* Header */}
        <div className="px-4 sm:px-6 py-3 border-b border-border-subtle flex items-center justify-between gap-3 flex-shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <button
              onClick={() => setIsSidebarOpen((o) => !o)}
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl border border-border-subtle bg-surface text-muted hover:text-foreground hover:bg-surface-2 transition-all cursor-pointer"
              title={isSidebarOpen ? "Collapse conversations" : "Show conversations"}
              aria-label="Toggle conversations"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="min-w-0">
              <h3 className="text-sm font-semibold text-foreground truncate max-w-[40vw]">{getActiveSessionTitle()}</h3>
              <p className="text-[9px] text-muted font-medium uppercase mt-0.5 tracking-wider">Tenant Session</p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {currentSessionId && (
              <button
                onClick={() => {
                  setCurrentSessionId(null);
                  setMessages([]);
                }}
                className="hidden sm:inline-flex text-[10px] px-2.5 py-1.5 rounded-lg bg-surface-2 hover:bg-surface border border-border-subtle text-muted hover:text-foreground hover:border-accent/30 transition-all cursor-pointer"
              >
                Close Session
              </button>
            )}
            <button
              onClick={() => setIsSourcesOpen(true)}
              className="inline-flex items-center gap-2 rounded-xl border border-border-subtle bg-surface px-3 py-1.5 text-xs font-semibold text-foreground hover:bg-surface-2 hover:border-accent/40 transition-all cursor-pointer"
              title="Manage sources"
            >
              <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <span className="hidden sm:inline">Sources</span>
              <span className="inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full bg-accent-soft text-accent text-[10px] font-bold border border-accent/30">
                {selectedCount}
              </span>
            </button>
          </div>
        </div>

        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {isLoadingMessages ? (
            <div className="h-full flex items-center justify-center flex-col gap-2">
              <div className="w-5 h-5 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-muted">Loading conversation history...</span>
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col justify-center items-center text-center px-4 max-w-md mx-auto">
              <div className="w-12 h-12 rounded-2xl bg-surface flex items-center justify-center border border-border-subtle mb-4 text-accent shadow-sm">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>

              {indexedCount === 0 ? (
                <>
                  <h4 className="text-sm font-semibold text-foreground">Add a source to get started</h4>
                  <p className="text-xs text-muted mt-1 mb-6 leading-relaxed">
                    Upload a PDF, paste text, or index a YouTube video. Then ask anything about it.
                  </p>
                  <button
                    onClick={() => setIsSourcesOpen(true)}
                    className="inline-flex items-center gap-2 rounded-full bg-foreground px-5 py-2.5 text-sm font-semibold text-background shadow-lg shadow-black/10 transition-all hover:opacity-90 cursor-pointer"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add sources
                  </button>
                </>
              ) : (
                <>
                  <h4 className="text-sm font-semibold text-foreground">How can I assist with your documents?</h4>
                  <p className="text-xs text-muted mt-1 mb-6 leading-relaxed">
                    Submit a question below to query the selected files in your tenant-isolated vector store.
                  </p>
                  <div className="grid grid-cols-2 gap-2.5 w-full">
                    {suggestions.map((sug, i) => (
                      <button
                        key={i}
                        onClick={() => sendMessage(sug)}
                        disabled={isLoading || isStreaming}
                        className="p-3 text-[11px] bg-surface hover:bg-surface-2 border border-border-subtle hover:border-accent/40 text-muted hover:text-foreground rounded-xl transition-all text-left font-medium leading-tight cursor-pointer"
                      >
                        {sug}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : (
            <div className="flex flex-col gap-4 max-w-3xl mx-auto w-full">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`p-4 rounded-2xl max-w-[85%] ${
                    msg.role === "user"
                      ? "bg-foreground text-background self-end ml-12 rounded-tr-none shadow-lg shadow-black/10"
                      : "bg-surface text-foreground self-start mr-12 rounded-tl-none border border-border-subtle shadow-sm"
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
                          <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
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
        <div className="p-4 border-t border-border-subtle flex-shrink-0">
          <div className="flex gap-2 max-w-3xl mx-auto w-full">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your sources..."
              className="flex-1 px-4 py-3 bg-surface border border-border-subtle rounded-xl focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent text-sm text-foreground placeholder-muted transition-all"
              disabled={isLoading || isStreaming || isLoadingMessages}
            />
            <button
              onClick={() => sendMessage()}
              disabled={isLoading || isStreaming || isLoadingMessages || !question.trim()}
              className="px-5 py-3 bg-foreground hover:opacity-90 disabled:bg-surface-2 text-background disabled:text-muted rounded-xl font-medium shadow-lg shadow-black/10 disabled:shadow-none disabled:opacity-60 disabled:cursor-not-allowed transition-all flex items-center justify-center cursor-pointer"
            >
              {isLoading || isStreaming ? (
                <div className="w-4 h-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4 transform rotate-90" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* ── Sources slide-over panel (declutters the rail) ───────── */}
      {isSourcesOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
          onClick={() => setIsSourcesOpen(false)}
        />
      )}
      <aside
        className={`
          fixed inset-y-0 right-0 z-50 flex h-full w-full sm:w-[420px] flex-col
          bg-surface border-l border-border-subtle shadow-2xl
          transition-transform duration-300 ease-in-out
          ${isSourcesOpen ? "translate-x-0" : "translate-x-full"}
        `}
        aria-hidden={!isSourcesOpen}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-border-subtle flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent-soft flex items-center justify-center text-accent">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground leading-tight">Sources</h3>
              <p className="text-[10px] text-muted leading-tight">{selectedCount} of {indexedCount} selected for retrieval</p>
            </div>
          </div>
          <button
            onClick={() => setIsSourcesOpen(false)}
            className="flex h-8 w-8 items-center justify-center rounded-lg border border-border-subtle text-muted hover:text-foreground hover:bg-surface-2 transition-all cursor-pointer"
            aria-label="Close sources"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-5">
          <FileUpload
            mode="sidebar"
            uploadedFiles={uploadedFiles}
            setUploadedFiles={setUploadedFiles}
            selectedFiles={selectedFiles}
            setSelectedFiles={setSelectedFiles}
            onFileClick={(filename) => {
              handleFileClick(filename);
              setIsSourcesOpen(false);
            }}
          />
        </div>
      </aside>

      {/* ── PDF Viewer Panel ──────────────────────────────────── */}
      {/* On desktop: right-side panel that expands inline.       */}
      {/* On mobile:  fixed overlay panel over the full screen.   */}
      <div
        className={`
          md:relative md:flex md:h-full transition-all duration-300
          ${
            activeCitation
              ? "fixed inset-y-0 right-0 z-40 w-full md:w-auto md:static md:z-auto"
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