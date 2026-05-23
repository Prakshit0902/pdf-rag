"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";

type JobStatus = "pending" | "processing" | "completed" | "failed";

interface JobState {
  jobId: string | null;
  status: JobStatus;
  filename: string;
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

export default function FileUpload({ mode = "card" }: { mode?: "sidebar" | "card" }) {
  const { getToken, isLoaded, userId } = useAuth();
  
  const [job, setJob] = useState<JobState>({
    jobId: null,
    status: "pending",
    filename: "",
    error: null,
  });
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<string[]>([]);
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
        setUploadedFiles(data.files || []);
      }
    } catch (err) {
      console.error("Error fetching files:", err);
    } finally {
      setIsLoadingFiles(false);
    }
  }, [userId, getToken]);

  useEffect(() => {
    if (isLoaded && userId) {
      fetchUploadedFiles();
    }
  }, [isLoaded, userId, fetchUploadedFiles]);

  const pollJobStatus = useCallback(async (jobId: string) => {
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
        setJob((prev) => ({
          ...prev,
          status: data.status,
          error: data.error,
        }));

        if (data.status === "processing" || data.status === "pending") {
          setTimeout(poll, 2000);
        } else if (data.status === "completed") {
          fetchUploadedFiles();
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    };

    poll();
  }, [getToken, fetchUploadedFiles]);

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setSelectedFile(file);

    const formData = new FormData();
    formData.append("file", file);

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
      setJob({
        jobId: data.job_id,
        status: data.status,
        filename: data.filename,
        error: null,
      });

      pollJobStatus(data.job_id);
    } catch (err) {
      setJob((prev) => ({
        ...prev,
        status: "failed",
        error: err instanceof Error ? err.message : "Upload failed",
      }));
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 50 * 1024 * 1024) {
        alert("File size exceeds 50MB limit");
        return;
      }
      if (file.type !== "application/pdf") {
        alert("Only PDF files are allowed");
        return;
      }
      uploadFile(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      if (file.size > 50 * 1024 * 1024) {
        alert("File size exceeds 50MB limit");
        return;
      }
      if (file.type !== "application/pdf") {
        alert("Only PDF files are allowed");
        return;
      }
      uploadFile(file);
    }
  };

  const reset = () => {
    setJob({ jobId: null, status: "pending", filename: "", error: null });
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getStatusColor = () => {
    switch (job.status) {
      case "completed":
        return "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]";
      case "failed":
        return "bg-rose-500 shadow-[0_0_10px_rgba(244,63,94,0.5)]";
      case "processing":
        return "bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)] animate-pulse";
      default:
        return "bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.5)]";
    }
  };

  const getStatusText = () => {
    switch (job.status) {
      case "completed":
        return "Index ready";
      case "failed":
        return "Failed";
      case "processing":
        return "Parsing & indexing...";
      default:
        return "Pending";
    }
  };

  const progress = job.status === "completed" ? 100 : job.status === "processing" ? 60 : job.status === "failed" ? 0 : 20;

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

      {!job.jobId ? (
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
                {mode === "sidebar" ? "Upload PDF" : "Select PDF or Drag & Drop"}
              </span>
            </div>
            {mode !== "sidebar" && <p className="text-xs text-zinc-600">Max file size 50MB</p>}
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 bg-zinc-950/50 border border-zinc-900 rounded-xl">
            <div className="w-8 h-8 bg-zinc-900 rounded-lg flex items-center justify-center border border-zinc-800 flex-shrink-0">
              <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-zinc-200 truncate">{job.filename}</p>
              <p className={`text-[10px] font-semibold mt-0.5 ${job.status === "completed" ? "text-emerald-400" : job.status === "failed" ? "text-rose-400" : "text-indigo-400"}`}>
                {getStatusText()}
              </p>
            </div>
          </div>

          <div className="w-full bg-zinc-950 rounded-full h-1 overflow-hidden">
            <div
              className={`h-1 rounded-full transition-all duration-500 ${getStatusColor()}`}
              style={{ width: `${progress}%` }}
            />
          </div>

          {job.error && (
            <p className="text-[10px] text-rose-400 p-2 bg-rose-950/20 border border-rose-900/30 rounded-xl">{job.error}</p>
          )}

          {job.status === "completed" && (
            <button
              onClick={reset}
              className="w-full py-2 px-3 bg-zinc-100 hover:bg-white text-zinc-950 font-semibold rounded-xl text-xs transition-colors cursor-pointer"
            >
              Upload Another PDF
            </button>
          )}
        </div>
      )}

      {isUploading && (
        <div className="text-center text-[10px] text-zinc-500 animate-pulse">Uploading file to server...</div>
      )}

      {/* Uploaded files catalog */}
      <div className={mode === "sidebar" ? "border-t border-zinc-900 pt-3" : "border-t border-zinc-900 pt-6"}>
        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider mb-2">Workspace Index Files</h4>
        {isLoadingFiles ? (
          <div className="text-zinc-600 text-xs py-1">Loading files...</div>
        ) : uploadedFiles.length === 0 ? (
          <p className="text-zinc-600 text-xs italic">No documents indexed.</p>
        ) : (
          <div className={`${mode === "sidebar" ? "max-h-36" : "max-h-48"} overflow-y-auto space-y-1.5 pr-1 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent`}>
            {uploadedFiles.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2 bg-zinc-950/30 hover:bg-zinc-950/60 border border-zinc-900/80 rounded-xl transition-all"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <svg className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-[11px] text-zinc-300 font-medium truncate">{file}</span>
                </div>
                <span className="text-[9px] px-1.5 py-0.2 rounded-full font-bold text-emerald-400 bg-emerald-950/20 border border-emerald-900/30 flex-shrink-0">
                  Active
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}