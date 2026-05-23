"use client";

import { useEffect, useState } from "react";
import { marked } from "marked";

interface MarkdownRendererProps {
  content: string;
  isStreaming?: boolean;
}

export default function MarkdownRenderer({ content, isStreaming = false }: MarkdownRendererProps) {
  const [html, setHtml] = useState("");

  useEffect(() => {
    marked.setOptions({
      breaks: true,
      gfm: true,
    });
    
    const parsed = marked.parse(content);
    if (parsed instanceof Promise) {
      parsed.then((resolved) => setHtml(resolved));
    } else {
      setHtml(parsed);
    }
  }, [content]);

  return (
    <div
      className={`markdown-content text-[12px] sm:text-xs text-zinc-300 leading-relaxed ${isStreaming ? "is-streaming" : ""}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}