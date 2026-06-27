"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";

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

export interface Citation {
  source: string;
  page: number;
  text: string;
}

interface PdfViewerPanelProps {
  citation: Citation | null;
  onClose: () => void;
}

export default function PdfViewerPanel({ citation, onClose }: PdfViewerPanelProps) {
  const { getToken } = useAuth();
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [txtContent, setTxtContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [isExcerptExpanded, setIsExcerptExpanded] = useState<boolean>(true);
  const [retryKey, setRetryKey] = useState<number>(0);

  // Sync the local page cursor whenever the citation changes
  useEffect(() => {
    if (citation) {
      setCurrentPage(citation.page);
      setIsExcerptExpanded(true); // Auto expand on new citation
    }
  }, [citation?.source, citation?.page]);

  // Fetch the raw PDF file and convert to blob URL once when file changes
  useEffect(() => {
    let active = true;
    let currentUrl: string | null = null;

    if (citation?.source) {
      setIsLoading(true);
      setLoadError(false);
      setPdfUrl(null);
      setTxtContent(null);

      const fetchFile = async () => {
        try {
          const token = await getToken();
          const headers: Record<string, string> = {};
          if (token) {
            headers["Authorization"] = `Bearer ${token}`;
          }

          const res = await fetch(
            `${API_BASE}/files/pdf?filename=${encodeURIComponent(citation.source)}`,
            { headers }
          );

          if (!res.ok) {
            if (active) setLoadError(true);
            return;
          }

          const isTxt = citation.source.toLowerCase().endsWith(".txt");
          if (isTxt) {
            const text = await res.text();
            if (active) {
              setTxtContent(text);
            }
          } else {
            const blob = await res.blob();
            if (active) {
              const objectUrl = URL.createObjectURL(blob);
              currentUrl = objectUrl;
              setPdfUrl(objectUrl);
            }
          }
        } catch {
          if (active) setLoadError(true);
        } finally {
          if (active) setIsLoading(false);
        }
      };

      fetchFile();
    }

    return () => {
      active = false;
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl);
      }
    };
  }, [citation?.source, getToken, retryKey]);

  // Panel is visible when citation is set
  const isOpen = citation !== null;

  return (
    <div
      className={`
        flex-shrink-0 flex flex-col h-full relative
        bg-[#323639] border-l border-border-subtle
        transition-all duration-300 ease-in-out overflow-hidden
        ${
          isOpen
            ? "w-[min(100vw,700px)] sm:w-[500px] md:w-[600px] lg:w-[680px] xl:w-[760px] 2xl:w-[860px] opacity-100"
            : "w-0 opacity-0 border-none"
        }
      `}
      aria-hidden={!isOpen}
    >
      {isOpen && citation && (
        <div className="flex flex-col h-full overflow-hidden">
          {/* ── PDF Panel Header (Minimal & Sleek, letting native PDF viewer controls stand out) ── */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-[#2d3134] border-b border-[#202224] text-zinc-300 flex-shrink-0 select-none shadow-md z-10">
            <div className="flex items-center gap-2 min-w-0">
              {/* File Icon */}
              <div className="w-7 h-7 rounded bg-[#202224] flex items-center justify-center flex-shrink-0 border border-zinc-700/30">
                {citation.source.toLowerCase().endsWith(".txt") ? (
                  <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4 text-red-500 fill-current" viewBox="0 0 24 24">
                    <path d="M11.362 2C7.656 2 6 3.656 6 7.362v9.276C6 20.344 7.656 22 11.362 22h1.276C16.344 22 18 20.344 18 16.638V7.362C18 3.656 16.344 2 12.638 2h-1.276zm0 2h1.276c2.518 0 3.362.844 3.362 3.362v9.276c0 2.518-.844 3.362-3.362 3.362h-1.276c-2.518 0-3.362-.844-3.362-3.362V7.362C8 4.844 8.844 4 11.362 4z" />
                  </svg>
                )}
              </div>
              <p className="text-xs font-semibold text-zinc-200 truncate max-w-[280px] md:max-w-[400px]" title={citation.source}>
                {citation.source}
              </p>
            </div>
            
            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-1.5 rounded hover:bg-red-500/10 text-zinc-400 hover:text-red-400 transition-all cursor-pointer border border-transparent hover:border-red-500/20"
              title="Close PDF viewer"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* ── Page Canvas Viewer (Loaded in native iframe for full select/scroll/zoom support) ── */}
          <div className="flex-1 w-full h-full bg-[#525659] relative overflow-hidden select-text">
            {isLoading ? (
              /* Loading skeleton */
              <div className="absolute inset-0 flex items-center justify-center p-8 bg-[#525659]">
                <div className="space-y-4 animate-pulse w-full max-w-[550px] shadow-2xl rounded-lg overflow-hidden bg-zinc-800/85 p-8 border border-zinc-700/50 aspect-[3/4.15]" />
              </div>
            ) : loadError ? (
              /* Error state */
              <div className="flex flex-col items-center justify-center h-full gap-4 text-center py-20 px-8 bg-[#525659]">
                <div className="w-16 h-16 rounded-2xl bg-[#323639] border border-zinc-700/40 flex items-center justify-center text-zinc-500 shadow-lg">
                  <svg className="w-8 h-8 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-zinc-300">PDF Load Failure</h4>
                  <p className="text-xs text-zinc-400 mt-1 max-w-[280px] leading-relaxed">
                    Could not load the PDF document from the server. Check backend logs.
                  </p>
                </div>
                <button
                  onClick={() => setRetryKey((k) => k + 1)}
                  className="text-xs px-4 py-2 rounded-xl bg-accent hover:bg-accent-strong text-accent-foreground font-semibold shadow-md transition-all cursor-pointer"
                >
                  Try Again
                </button>
              </div>
            ) : pdfUrl && !citation.source.toLowerCase().endsWith(".txt") ? (
              /* PDF iframe with native PDF Viewer controls (zoom, page count scroll sync are native to the browser) */
              <iframe
                key={`${citation.source}-${currentPage}-${retryKey}`}
                src={`${pdfUrl}#page=${currentPage}`}
                className="w-full h-full border-none bg-[#525659]"
                title={`PDF Viewer - ${citation.source}`}
              />
            ) : citation.source.startsWith("YouTube -") ? (
              /* YouTube Iframe viewer */
              <iframe
                key={`${citation.source}-${currentPage}-${retryKey}`}
                src={`https://www.youtube.com/embed/${citation.source.match(/\((.{11})\)\.txt/)?.[1] || ""}?start=${currentPage}&autoplay=1`}
                className="w-full h-full border-none bg-black"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                title={`YouTube Viewer - ${citation.source}`}
              />
            ) : txtContent ? (
              /* Plain Text Viewer */
              <div className="w-full h-full overflow-y-auto p-8 bg-[#18181b] text-zinc-300 font-mono text-sm leading-relaxed whitespace-pre-wrap select-text">
                {txtContent}
              </div>
            ) : null}

            {/* ── Collapsible Citation Overlay Drawer (floating at bottom) ───── */}
            {citation.text && (
              <div
                className={`
                  absolute bottom-6 left-6 right-6 z-20 flex flex-col
                  bg-zinc-900/95 backdrop-blur-md border border-zinc-800 rounded-xl shadow-2xl
                  transition-all duration-300 max-w-xl mx-auto
                `}
              >
                {/* Header / Toggle button */}
                <button
                  onClick={() => setIsExcerptExpanded((ex) => !ex)}
                  className="flex items-center justify-between px-4 py-3 text-left text-zinc-300 hover:text-white cursor-pointer select-none"
                >
                  <span className="text-xs font-bold flex items-center gap-2 text-amber-400">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                    </svg>
                    Retrieved Passage Context
                  </span>
                  <span className="text-[10px] text-zinc-500 flex items-center gap-1 font-semibold">
                    {isExcerptExpanded ? "HIDE" : "SHOW"}
                    <svg
                      className={`w-3.5 h-3.5 transform transition-transform duration-200 ${
                        isExcerptExpanded ? "rotate-180" : ""
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M19 9l-7 7-7-7" />
                    </svg>
                  </span>
                </button>

                {/* Expanded content */}
                {isExcerptExpanded && (
                  <div className="px-4 pb-4 border-t border-zinc-800/60 pt-3 select-text">
                    <div className="bg-amber-950/20 border-l-2 border-amber-500/60 pl-3 pr-2 py-2 rounded-r-lg max-h-36 overflow-y-auto scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
                      <p className="text-[11px] text-zinc-300 leading-relaxed italic pr-1">
                        &ldquo;{citation.text}&rdquo;
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
