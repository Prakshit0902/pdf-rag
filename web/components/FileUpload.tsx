"use client";

import { useState, useRef } from "react";


type JobStatus = "pending" | "processing" | "completed" | "failed";

interface JobState {
  jobId: string | null;
  status: JobStatus;
  filename: string;
  error: string | null;
}

export default function FileUpload() {
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const [job, setJob] = useState<JobState>({
    jobId: null,
    status: "pending",
    filename: "",
    error: null,
  });
  const [isUploading, setIsUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setSelectedFile(file);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
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

  const pollJobStatus = async (jobId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/upload/status/${jobId}`);
        if (!response.ok) throw new Error("Failed to fetch status");

        const data = await response.json();
        setJob((prev) => ({
          ...prev,
          status: data.status,
          error: data.error,
        }));

        if (data.status === "processing" || data.status === "pending") {
          setTimeout(poll, 2000);
        }
      } catch (err) {
        console.error("Polling error:", err);
      }
    };

    poll();
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
        return "bg-green-500";
      case "failed":
        return "bg-red-500";
      case "processing":
        return "bg-blue-500";
      default:
        return "bg-yellow-500";
    }
  };

  const getStatusText = () => {
    switch (job.status) {
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      case "processing":
        return "Processing...";
      default:
        return "Pending";
    }
  };

  const progress = job.status === "completed" ? 100 : job.status === "processing" ? 60 : job.status === "failed" ? 0 : 20;

  return (
    <div className="w-full max-w-md p-6 bg-white rounded-lg shadow-md border border-zinc-200">
      <h2 className="text-xl font-semibold mb-4 text-zinc-800">Upload PDF</h2>

      {!job.jobId ? (
        <div
          className="border-2 border-dashed border-zinc-300 rounded-lg p-8 text-center cursor-pointer hover:border-zinc-400 transition-colors"
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
          <div className="text-zinc-500">
            <p className="font-medium">Click to upload or drag and drop</p>
            <p className="text-sm mt-1">PDF only, max 50MB</p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-3 bg-zinc-50 rounded-lg">
            <div className="w-10 h-10 bg-zinc-200 rounded flex items-center justify-center">
              <svg className="w-5 h-5 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-zinc-800 truncate">{job.filename}</p>
              <p className={`text-xs font-medium ${job.status === "completed" ? "text-green-600" : job.status === "failed" ? "text-red-600" : "text-zinc-500"}`}>
                {getStatusText()}
              </p>
            </div>
          </div>

          <div className="w-full bg-zinc-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${getStatusColor()}`}
              style={{ width: `${progress}%` }}
            />
          </div>

          {job.error && (
            <p className="text-sm text-red-600 p-2 bg-red-50 rounded">{job.error}</p>
          )}

          {job.status === "completed" && (
            <button
              onClick={reset}
              className="w-full py-2 px-4 bg-zinc-900 text-white rounded-lg hover:bg-zinc-800 transition-colors"
            >
              Upload Another File
            </button>
          )}
        </div>
      )}

      {isUploading && (
        <div className="mt-4 text-center text-sm text-zinc-500">Uploading...</div>
      )}
    </div>
  );
}