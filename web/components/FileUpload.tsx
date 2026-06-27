"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";

type JobStatus = "queued" | "uploading" | "processing" | "completed" | "failed";

interface UploadTask {
  id: string;
  file: File | null;
  filename: string;
  status: JobStatus;
  progress: number;
  jobId: string | null;
  error: string | null;
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

export default function FileUpload({
  mode = "card",
  uploadedFiles,
  setUploadedFiles,
  selectedFiles,
  setSelectedFiles,
  onFileClick,
}: {
  mode?: "sidebar" | "card";
  uploadedFiles: string[];
  setUploadedFiles: React.Dispatch<React.SetStateAction<string[]>>;
  selectedFiles: string[];
  setSelectedFiles: React.Dispatch<React.SetStateAction<string[]>>;
  /** Called when user clicks the preview icon on an indexed file */
  onFileClick?: (filename: string) => void;
}) {
  const { getToken, isLoaded, userId } = useAuth();
  
  const [activeTab, setActiveTab] = useState<"files" | "paste" | "youtube">("files");
  const [pasteTitle, setPasteTitle] = useState("");
  const [pasteText, setPasteText] = useState("");
  const [ytUrl, setYtUrl] = useState("");
  const [isSubmittingYt, setIsSubmittingYt] = useState(false);

  const [uploadTasks, setUploadTasks] = useState<UploadTask[]>([]);
  const [isLoadingFiles, setIsLoadingFiles] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchUploadedFiles = useCallback(async () => {
    if (!userId) return;
    setIsLoadingFiles(true);
    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/upload/files`, { headers });
      if (response.ok) {
        const data = await response.json();
        const files = data.files || [];
        setUploadedFiles(files);
        // Automatically select all files by default if none are currently selected
        setSelectedFiles(prev => {
          if (prev.length === 0 && files.length > 0) {
            return files;
          }
          return prev;
        });
      }
    } catch (err) {
      console.error("Error fetching files:", err);
    } finally {
      setIsLoadingFiles(false);
    }
  }, [userId, getToken, setUploadedFiles, setSelectedFiles]);

  useEffect(() => {
    if (isLoaded && userId) {
      fetchUploadedFiles();
    }
  }, [isLoaded, userId, fetchUploadedFiles]);

  // Update specific task state helper
  const updateTaskStatus = (id: string, updates: Partial<UploadTask>) => {
    setUploadTasks((prev) =>
      prev.map((t) => (t.id === id ? { ...t, ...updates } : t))
    );
  };

  // Poll background job status for a task
  const pollTaskStatus = useCallback(async (taskId: string, jobId: string) => {
    const poll = async () => {
      try {
        const token = await getToken();
        const headers: Record<string, string> = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const response = await fetch(`${API_BASE}/upload/status/${jobId}`, { headers });
        if (!response.ok) throw new Error("Failed to fetch status");

        const data = await response.json();
        
        if (data.status === "processing" || data.status === "pending") {
          updateTaskStatus(taskId, {
            status: "processing",
            progress: data.status === "processing" ? 75 : 40,
          });
          setTimeout(poll, 2000);
        } else if (data.status === "completed") {
          updateTaskStatus(taskId, {
            status: "completed",
            progress: 100,
            filename: data.filename,
          });
          // Refresh catalog
          fetchUploadedFiles();
          // Automatically add new file to selection
          setSelectedFiles((prev) => 
            prev.includes(data.filename) ? prev : [...prev, data.filename]
          );
        } else if (data.status === "failed") {
          updateTaskStatus(taskId, {
            status: "failed",
            progress: 0,
            error: data.error || "Processing failed",
          });
        }
      } catch (err) {
        console.error("Polling error:", err);
        updateTaskStatus(taskId, {
          status: "failed",
          progress: 0,
          error: err instanceof Error ? err.message : "Polling failed",
        });
      }
    };

    poll();
  }, [getToken, fetchUploadedFiles, setSelectedFiles]);

  // Upload file pipeline runner
  const uploadFileTask = useCallback(async (task: UploadTask) => {
    if (task.jobId) {
      updateTaskStatus(task.id, { status: "processing", progress: 40 });
      pollTaskStatus(task.id, task.jobId);
      return;
    }

    updateTaskStatus(task.id, { status: "uploading", progress: 15 });

    if (!task.file) {
      updateTaskStatus(task.id, { status: "failed", error: "No file provided" });
      return;
    }

    const formData = new FormData();
    formData.append("file", task.file);

    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Upload failed");
      }

      const data = await response.json();
      
      if (data.status === "cached") {
        updateTaskStatus(task.id, {
          status: "completed",
          progress: 100,
          jobId: null,
        });
        fetchUploadedFiles();
        // Automatically add cached file to selection
        setSelectedFiles((prev) => 
          prev.includes(task.filename) ? prev : [...prev, task.filename]
        );
      } else {
        updateTaskStatus(task.id, {
          status: "processing",
          progress: 40,
          jobId: data.job_id,
        });
        pollTaskStatus(task.id, data.job_id);
      }
    } catch (err) {
      updateTaskStatus(task.id, {
        status: "failed",
        progress: 0,
        error: err instanceof Error ? err.message : "Upload failed",
      });
    }
  }, [getToken, pollTaskStatus, fetchUploadedFiles, setSelectedFiles]);

  // Find the active task (uploading or processing)
  const activeTask = uploadTasks.find(
    (t) => t.status === "uploading" || t.status === "processing"
  );
  // Find the next queued task
  const nextTask = uploadTasks.find((t) => t.status === "queued");

  // Effect to automatically run the queue sequentially
  useEffect(() => {
    if (!activeTask && nextTask) {
      uploadFileTask(nextTask);
    }
  }, [uploadTasks, activeTask, nextTask, uploadFileTask]);

  const handleFilesSelected = (files: FileList) => {
    const newTasks: UploadTask[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (file.size > 50 * 1024 * 1024) {
        alert(`File ${file.name} exceeds 50MB limit`);
        continue;
      }
      
      const isPdf = file.type === "application/pdf" || file.name.endsWith(".pdf");
      const isTxt = file.type === "text/plain" || file.name.endsWith(".txt");
      const isDocx = file.name.endsWith(".docx");
      const isPptx = file.name.endsWith(".pptx");
      if (!isPdf && !isTxt && !isDocx && !isPptx) {
        alert(`Only PDF, TXT, DOCX, and PPTX files are allowed. Skipped ${file.name}`);
        continue;
      }
      
      const taskId = `${file.name}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      newTasks.push({
        id: taskId,
        file,
        filename: file.name,
        status: "queued",
        progress: 0,
        jobId: null,
        error: null,
      });
    }

    if (newTasks.length > 0) {
      setUploadTasks((prev) => [...prev, ...newTasks]);
    }
  };

  const handlePasteSubmit = (title: string, text: string) => {
    if (!title.trim()) {
      alert("Please enter a title for your pasted text.");
      return;
    }
    if (!text.trim()) {
      alert("Please paste some text content.");
      return;
    }

    let filename = title.trim();
    if (!filename.toLowerCase().endsWith(".txt")) {
      filename += ".txt";
    }

    const blob = new Blob([text], { type: "text/plain" });
    const file = new File([blob], filename, { type: "text/plain" });

    const taskId = `${filename}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newTask: UploadTask = {
      id: taskId,
      file,
      filename,
      status: "queued",
      progress: 0,
      jobId: null,
      error: null,
    };

    setUploadTasks((prev) => [...prev, newTask]);
  };

  const handleYoutubeSubmit = async (url: string) => {
    if (!url.trim()) {
      alert("Please enter a YouTube video URL.");
      return;
    }
    
    setIsSubmittingYt(true);
    try {
      const token = await getToken();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      
      const response = await fetch(`${API_BASE}/upload/youtube`, {
        method: "POST",
        headers,
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to start YouTube processing");
      }

      const data = await response.json();
      
      if (data.warning) {
        alert(data.warning);
      }
      
      const taskId = `youtube-${data.job_id || Date.now()}`;
      const newTask: UploadTask = {
        id: taskId,
        file: null,
        filename: data.filename || `youtube_${Date.now()}`,
        status: "queued",
        progress: 0,
        jobId: data.job_id,
        error: null,
      };

      setUploadTasks((prev) => [...prev, newTask]);
      setYtUrl(""); // Reset input

    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to process YouTube URL");
    } finally {
      setIsSubmittingYt(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      handleFilesSelected(files);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files) {
      handleFilesSelected(files);
    }
  };

  const handleDeleteFile = async (file: string) => {
    if (
      !confirm(
        `Are you sure you want to permanently delete "${file}"? This will delete all related chat sessions.`
      )
    ) {
      return;
    }
    try {
      const token = await getToken();
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const response = await fetch(
        `${API_BASE}/upload/files/${encodeURIComponent(file)}`,
        {
          method: "DELETE",
          headers,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Delete failed");
      }

      // Remove from selected files list if it was selected
      setSelectedFiles((prev) => prev.filter((f) => f !== file));
      // Refresh documents catalog
      fetchUploadedFiles();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete file");
    }
  };

  const handleToggleFile = (file: string) => {
    setSelectedFiles((prev) =>
      prev.includes(file)
        ? prev.filter((f) => f !== file)
        : [...prev, file]
    );
  };

  const handleSelectAll = () => {
    setSelectedFiles(uploadedFiles);
  };

  const handleDeselectAll = () => {
    setSelectedFiles([]);
  };

  const clearTask = (id: string) => {
    setUploadTasks((prev) => prev.filter((t) => t.id !== id));
  };

  const clearAllTasks = () => {
    setUploadTasks([]);
  };

  return (
    <div className={`w-full ${mode === "sidebar" ? "space-y-3" : "bg-surface backdrop-blur-md rounded-2xl p-6 border border-border-subtle shadow-xl space-y-5"}`}>
      {mode === "sidebar" ? (
        <div className="flex items-center justify-between">
          <h3 className="text-[10px] font-bold text-muted uppercase tracking-wider flex items-center gap-2">
            <svg className="w-3.5 h-3.5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Workspace Documents
          </h3>
        </div>
      ) : (
        <div>
          <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
            <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Documents
          </h2>
          <p className="text-muted text-xs mt-1">Upload files to populate your knowledge base.</p>
        </div>
      )}

      {/* Tabs Menu */}
      <div className="flex border-b border-border-subtle text-[11px] font-semibold">
        <button
          onClick={() => setActiveTab("files")}
          className={`flex-1 pb-1.5 text-center border-b-2 transition-all cursor-pointer ${
            activeTab === "files"
              ? "border-accent text-foreground"
              : "border-transparent text-muted hover:text-foreground"
          }`}
        >
          Files
        </button>
        <button
          onClick={() => setActiveTab("paste")}
          className={`flex-1 pb-1.5 text-center border-b-2 transition-all cursor-pointer ${
            activeTab === "paste"
              ? "border-accent text-foreground"
              : "border-transparent text-muted hover:text-foreground"
          }`}
        >
          Paste Text
        </button>
        <button
          onClick={() => setActiveTab("youtube")}
          className={`flex-1 pb-1.5 text-center border-b-2 transition-all cursor-pointer ${
            activeTab === "youtube"
              ? "border-accent text-foreground"
              : "border-transparent text-muted hover:text-foreground"
          }`}
        >
          YouTube
        </button>
      </div>

      {/* Tab Contents */}
      {activeTab === "files" && (
        <div
          className={`border border-dashed border-border-subtle rounded-xl text-center cursor-pointer hover:border-accent/50 hover:bg-accent-soft/40 transition-all duration-300 group ${
            mode === "sidebar" ? "p-4" : "p-8"
          }`}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.docx,.pptx"
            multiple
            className="hidden"
            onChange={handleFileChange}
          />
          <div className="space-y-2">
            {mode !== "sidebar" && (
              <div className="w-12 h-12 rounded-xl bg-surface-2 flex items-center justify-center mx-auto border border-border-subtle group-hover:border-accent/40 group-hover:bg-accent-soft transition-all duration-300">
                <svg className="w-6 h-6 text-muted group-hover:text-accent transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
            )}
            <div className="text-muted flex items-center justify-center gap-2">
              {mode === "sidebar" && (
                <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              )}
              <span className="font-semibold text-xs group-hover:text-foreground transition-colors">
                {mode === "sidebar" ? "Upload PDF / TXT / DOCX / PPTX" : "Select PDF / TXT / DOCX / PPTX or Drag & Drop"}
              </span>
            </div>
            {mode !== "sidebar" && <p className="text-xs text-muted/70">Max file size 50MB per file</p>}
          </div>
        </div>
      )}

      {activeTab === "paste" && (
        <div className="space-y-2 bg-surface-2/40 p-1 rounded-xl">
          <input
            type="text"
            placeholder="Document Title (e.g. notes.txt)"
            value={pasteTitle}
            onChange={(e) => setPasteTitle(e.target.value)}
            className="w-full px-3 py-2 bg-surface-2 border border-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent text-xs text-foreground placeholder-muted transition-all"
          />
          <textarea
            placeholder="Paste your text context here..."
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            rows={mode === "sidebar" ? 4 : 6}
            className="w-full px-3 py-2 bg-surface-2 border border-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-accent/50 focus:border-accent text-xs text-foreground placeholder-muted resize-none font-sans transition-all"
          />
          <button
            onClick={() => {
              handlePasteSubmit(pasteTitle, pasteText);
              setPasteTitle("");
              setPasteText("");
            }}
            disabled={!pasteTitle.trim() || !pasteText.trim()}
            className="w-full py-2 bg-foreground hover:opacity-90 disabled:bg-surface-2 text-background disabled:text-muted rounded-xl text-xs font-bold shadow-md disabled:shadow-none disabled:opacity-60 transition-all cursor-pointer flex items-center justify-center gap-1.5"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
            </svg>
            Add Text Context
          </button>
        </div>
      )}

      {activeTab === "youtube" && (
        <div className="space-y-3 p-3 bg-surface-2/40 border border-border-subtle rounded-xl">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
              <svg className="w-4 h-4 text-rose-500 fill-current" viewBox="0 0 24 24">
                <path d="M23.498 6.163a3.003 3.003 0 0 0-2.11-2.108C19.524 3.545 12 3.545 12 3.545s-7.525 0-9.388.51a3.002 3.002 0 0 0-2.11 2.108C0 8.028 0 12 0 12s0 3.972.502 5.837a3.003 3.003 0 0 0 2.11 2.108c1.863.51 9.388.51 9.388.51s7.525 0 9.388-.51a3.002 3.002 0 0 0 2.11-2.108C24 15.972 24 12 24 12s0-3.972-.502-5.837zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" />
              </svg>
            </div>
            <div className="min-w-0">
              <h4 className="text-xs font-semibold text-foreground">YouTube Indexer</h4>
              <p className="text-[10px] text-muted truncate">Extract transcripts and index videos.</p>
            </div>
          </div>
          
          <input
            type="text"
            value={ytUrl}
            onChange={(e) => setYtUrl(e.target.value)}
            disabled={isSubmittingYt}
            placeholder="YouTube Video URL (e.g. https://youtu.be/...)"
            className="w-full px-3 py-2 bg-surface-2 border border-border-subtle rounded-xl focus:outline-none focus:ring-1 focus:ring-rose-500/50 focus:border-rose-500 text-xs text-foreground placeholder-muted transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          />
          
          <button
            onClick={() => handleYoutubeSubmit(ytUrl)}
            disabled={isSubmittingYt || !ytUrl.trim()}
            className="w-full py-2 bg-rose-600 hover:bg-rose-500 disabled:bg-surface-2 text-white disabled:text-muted rounded-xl text-xs font-bold shadow-md disabled:shadow-none hover:shadow-[0_0_12px_rgba(244,63,94,0.25)] transition-all cursor-pointer flex items-center justify-center gap-1.5"
          >
            {isSubmittingYt ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white/80" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Initiating...
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                Summarize Video
              </>
            )}
          </button>
        </div>
      )}

      {/* Upload Tasks Queue List */}
      {uploadTasks.length > 0 && (
        <div className="space-y-2 bg-surface-2/40 p-3 rounded-xl border border-border-subtle">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-bold text-muted uppercase tracking-wider">
              Upload Queue ({uploadTasks.filter(t => t.status === "completed").length}/{uploadTasks.length})
            </span>
            <button
              onClick={clearAllTasks}
              className="text-[9px] font-semibold text-muted hover:text-foreground transition-colors cursor-pointer"
            >
              Clear All
            </button>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {uploadTasks.map((task) => (
              <div key={task.id} className="p-2.5 bg-surface border border-border-subtle rounded-xl space-y-2 relative">
                <div className="flex items-center justify-between gap-2 min-w-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <svg className="w-3.5 h-3.5 text-accent flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="text-[11px] text-foreground font-semibold truncate">{task.filename}</span>
                  </div>
                  
                  <button
                    onClick={() => clearTask(task.id)}
                    className="text-muted hover:text-foreground w-4 h-4 rounded hover:bg-surface-2 flex items-center justify-center transition-colors cursor-pointer"
                    title="Remove"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="flex items-center justify-between text-[9px] font-medium">
                  <span className={`font-semibold ${
                    task.status === "completed" ? "text-emerald-500" :
                    task.status === "failed" ? "text-rose-500" :
                    task.status === "uploading" ? "text-accent" :
                    task.status === "processing" ? "text-amber-500" : "text-muted"
                  }`}>
                    {task.status === "completed" && "Index ready"}
                    {task.status === "failed" && "Failed"}
                    {task.status === "uploading" && "Uploading..."}
                    {task.status === "processing" && "Parsing & indexing..."}
                    {task.status === "queued" && "Queued"}
                  </span>
                  <span className="text-muted">{task.progress}%</span>
                </div>

                <div className="w-full bg-surface-2 rounded-full h-1 overflow-hidden">
                  <div
                    className={`h-1 rounded-full transition-all duration-350 ${
                      task.status === "completed" ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" :
                      task.status === "failed" ? "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]" :
                      task.status === "uploading" ? "bg-accent shadow-[0_0_10px_var(--accent-glow)] animate-pulse" :
                      task.status === "processing" ? "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)] animate-pulse" : "bg-surface-2"
                    }`}
                    style={{ width: `${task.progress}%` }}
                  />
                </div>

                {task.error && (
                  <p className="text-[9px] text-rose-500 leading-tight bg-rose-500/10 border border-rose-500/20 p-1.5 rounded-lg">
                    {task.error}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Uploaded files catalog */}
      <div className={mode === "sidebar" ? "border-t border-border-subtle pt-3" : "border-t border-border-subtle pt-6"}>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-[10px] font-bold text-muted uppercase tracking-wider">Workspace Index Files</h4>
          {uploadedFiles.length > 0 && (
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleSelectAll}
                className="text-[9px] text-accent hover:text-accent-strong font-bold transition-colors cursor-pointer"
              >
                All
              </button>
              <span className="text-border-subtle text-[8px] font-bold">|</span>
              <button
                onClick={handleDeselectAll}
                className="text-[9px] text-muted hover:text-foreground font-bold transition-colors cursor-pointer"
              >
                None
              </button>
            </div>
          )}
        </div>
        {isLoadingFiles ? (
          <div className="text-muted text-xs py-1">Loading files...</div>
        ) : uploadedFiles.length === 0 ? (
          <p className="text-muted text-xs italic">No documents indexed.</p>
        ) : (
          <div className={`${mode === "sidebar" ? "max-h-36" : "max-h-48"} overflow-y-auto space-y-1.5 pr-1`}>
            {uploadedFiles.map((file, idx) => {
              const isSelected = selectedFiles.includes(file);
              return (
                <div
                  key={idx}
                  onClick={() => handleToggleFile(file)}
                  className={`flex items-center justify-between p-2 rounded-xl transition-all cursor-pointer border ${
                    isSelected
                      ? "bg-accent-soft hover:bg-accent-soft border-accent/25"
                      : "bg-surface-2/40 hover:bg-surface-2 border-border-subtle opacity-70 hover:opacity-100"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className={`w-4 h-4 rounded flex items-center justify-center border transition-all ${
                      isSelected
                        ? "bg-accent border-accent text-accent-foreground shadow-[0_0_8px_var(--accent-glow)]"
                        : "border-border-subtle bg-transparent text-transparent"
                    }`}>
                      <svg className="w-2.5 h-2.5 animate-fade-in" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className={`text-[11px] font-medium truncate ${isSelected ? "text-foreground" : "text-muted"}`}>
                      {file}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold border transition-all ${
                      isSelected
                        ? "text-emerald-500 bg-emerald-500/10 border-emerald-500/20"
                        : "text-muted bg-surface-2 border-border-subtle"
                    }`}>
                      {isSelected ? "Active" : "Scoped"}
                    </span>
                    {/* Preview PDF button */}
                    {onFileClick && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onFileClick(file);
                        }}
                        className="text-muted hover:text-accent w-5 h-5 rounded hover:bg-accent-soft flex items-center justify-center transition-colors cursor-pointer"
                        title="Preview PDF"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteFile(file);
                      }}
                      className="text-muted hover:text-rose-500 w-5 h-5 rounded hover:bg-rose-500/10 flex items-center justify-center transition-colors cursor-pointer"
                      title="Delete document"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}