"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";

type JobStatus = "queued" | "uploading" | "processing" | "completed" | "failed";

interface UploadTask {
  id: string;
  file: File;
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

export default function FileUpload({
  mode = "card",
  uploadedFiles,
  setUploadedFiles,
  selectedFiles,
  setSelectedFiles
}: {
  mode?: "sidebar" | "card";
  uploadedFiles: string[];
  setUploadedFiles: React.Dispatch<React.SetStateAction<string[]>>;
  selectedFiles: string[];
  setSelectedFiles: React.Dispatch<React.SetStateAction<string[]>>;
}) {
  const { getToken, isLoaded, userId } = useAuth();
  
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
    updateTaskStatus(task.id, { status: "uploading", progress: 15 });

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
      if (file.type !== "application/pdf" && !file.name.endsWith(".pdf")) {
        alert(`Only PDF files are allowed. Skipped ${file.name}`);
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
    <div className={`w-full ${mode === "sidebar" ? "space-y-4" : "bg-zinc-900/40 backdrop-blur-md rounded-2xl p-6 border border-zinc-800/80 shadow-xl space-y-6"}`}>
      {mode === "sidebar" ? (
        <div className="flex items-center justify-between">
          <h3 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider flex items-center gap-2">
            <svg className="w-3.5 h-3.5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Workspace Documents
          </h3>
        </div>
      ) : (
        <div>
          <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <svg className="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            Documents
          </h2>
          <p className="text-zinc-500 text-xs mt-1">Upload files to populate your knowledge base.</p>
        </div>
      )}

      {/* Drag & Drop Area */}
      <div
        className={`border border-dashed border-zinc-800 rounded-xl text-center cursor-pointer hover:border-zinc-700 hover:bg-zinc-900/20 transition-all duration-300 group ${
          mode === "sidebar" ? "p-4" : "p-8"
        }`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />
        <div className="space-y-2">
          {mode !== "sidebar" && (
            <div className="w-12 h-12 rounded-xl bg-zinc-950 flex items-center justify-center mx-auto border border-zinc-900 group-hover:border-indigo-500/30 group-hover:bg-indigo-950/20 transition-all duration-300">
              <svg className="w-6 h-6 text-zinc-500 group-hover:text-indigo-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
          )}
          <div className="text-zinc-400 flex items-center justify-center gap-2">
            {mode === "sidebar" && (
              <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            )}
            <span className="font-semibold text-xs group-hover:text-zinc-200 transition-colors">
              {mode === "sidebar" ? "Upload PDFs" : "Select PDFs or Drag & Drop"}
            </span>
          </div>
          {mode !== "sidebar" && <p className="text-xs text-zinc-600">Max file size 50MB per file</p>}
        </div>
      </div>

      {/* Upload Tasks Queue List */}
      {uploadTasks.length > 0 && (
        <div className="space-y-2 bg-zinc-950/20 p-3 rounded-xl border border-zinc-800/40">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
              Upload Queue ({uploadTasks.filter(t => t.status === "completed").length}/{uploadTasks.length})
            </span>
            <button
              onClick={clearAllTasks}
              className="text-[9px] font-semibold text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer"
            >
              Clear All
            </button>
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
            {uploadTasks.map((task) => (
              <div key={task.id} className="p-2.5 bg-zinc-950/60 border border-zinc-900 rounded-xl space-y-2 relative">
                <div className="flex items-center justify-between gap-2 min-w-0">
                  <div className="flex items-center gap-2 min-w-0">
                    <svg className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="text-[11px] text-zinc-200 font-semibold truncate">{task.filename}</span>
                  </div>
                  
                  <button
                    onClick={() => clearTask(task.id)}
                    className="text-zinc-500 hover:text-zinc-300 w-4 h-4 rounded hover:bg-zinc-900 flex items-center justify-center transition-colors cursor-pointer"
                    title="Remove"
                  >
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="flex items-center justify-between text-[9px] font-medium">
                  <span className={`font-semibold ${
                    task.status === "completed" ? "text-emerald-400" :
                    task.status === "failed" ? "text-rose-400" :
                    task.status === "uploading" ? "text-indigo-400" :
                    task.status === "processing" ? "text-amber-400" : "text-zinc-500"
                  }`}>
                    {task.status === "completed" && "Index ready"}
                    {task.status === "failed" && "Failed"}
                    {task.status === "uploading" && "Uploading..."}
                    {task.status === "processing" && "Parsing & indexing..."}
                    {task.status === "queued" && "Queued"}
                  </span>
                  <span className="text-zinc-500">{task.progress}%</span>
                </div>

                <div className="w-full bg-zinc-950 rounded-full h-1 overflow-hidden">
                  <div
                    className={`h-1 rounded-full transition-all duration-350 ${
                      task.status === "completed" ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" :
                      task.status === "failed" ? "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]" :
                      task.status === "uploading" ? "bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)] animate-pulse" :
                      task.status === "processing" ? "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)] animate-pulse" : "bg-zinc-800"
                    }`}
                    style={{ width: `${task.progress}%` }}
                  />
                </div>

                {task.error && (
                  <p className="text-[9px] text-rose-400 leading-tight bg-rose-950/20 border border-rose-900/30 p-1.5 rounded-lg">
                    {task.error}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Uploaded files catalog */}
      <div className={mode === "sidebar" ? "border-t border-zinc-900 pt-3" : "border-t border-zinc-900 pt-6"}>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">Workspace Index Files</h4>
          {uploadedFiles.length > 0 && (
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleSelectAll}
                className="text-[9px] text-indigo-400 hover:text-indigo-300 font-bold transition-colors cursor-pointer"
              >
                All
              </button>
              <span className="text-zinc-800 text-[8px] font-bold">|</span>
              <button
                onClick={handleDeselectAll}
                className="text-[9px] text-zinc-500 hover:text-zinc-300 font-bold transition-colors cursor-pointer"
              >
                None
              </button>
            </div>
          )}
        </div>
        {isLoadingFiles ? (
          <div className="text-zinc-600 text-xs py-1">Loading files...</div>
        ) : uploadedFiles.length === 0 ? (
          <p className="text-zinc-600 text-xs italic">No documents indexed.</p>
        ) : (
          <div className={`${mode === "sidebar" ? "max-h-36" : "max-h-48"} overflow-y-auto space-y-1.5 pr-1 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent`}>
            {uploadedFiles.map((file, idx) => {
              const isSelected = selectedFiles.includes(file);
              return (
                <div
                  key={idx}
                  onClick={() => handleToggleFile(file)}
                  className={`flex items-center justify-between p-2 rounded-xl transition-all cursor-pointer border ${
                    isSelected
                      ? "bg-indigo-950/15 hover:bg-indigo-950/25 border-indigo-500/20"
                      : "bg-zinc-950/10 hover:bg-zinc-950/25 border-zinc-900/60 opacity-60 hover:opacity-85"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className={`w-4 h-4 rounded flex items-center justify-center border transition-all ${
                      isSelected
                        ? "bg-indigo-600 border-indigo-500 text-white shadow-[0_0_8px_rgba(99,102,241,0.4)]"
                        : "border-zinc-700 bg-transparent text-transparent"
                    }`}>
                      <svg className="w-2.5 h-2.5 animate-fade-in" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <span className={`text-[11px] font-medium truncate ${isSelected ? "text-zinc-200" : "text-zinc-400"}`}>
                      {file}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`text-[9px] px-1.5 py-0.2 rounded-full font-bold border transition-all ${
                      isSelected
                        ? "text-emerald-400 bg-emerald-950/20 border-emerald-900/30"
                        : "text-zinc-500 bg-zinc-950/40 border-zinc-900"
                    }`}>
                      {isSelected ? "Active" : "Scoped"}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteFile(file);
                      }}
                      className="text-zinc-500 hover:text-rose-400 w-5 h-5 rounded hover:bg-zinc-900/50 flex items-center justify-center transition-colors cursor-pointer"
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