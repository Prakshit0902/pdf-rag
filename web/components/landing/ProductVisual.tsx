"use client";

import React from "react";
import { motion } from "framer-motion";
import { FileText, Video, Presentation, Quote, Sparkles } from "lucide-react";

const sources = [
  { icon: FileText, name: "Annual_Report.pdf", meta: "84 pages", active: true },
  { icon: Presentation, name: "Strategy_2026.pptx", meta: "32 slides", active: false },
  { icon: Video, name: "Investor call", meta: "58:21", active: false },
];

export default function ProductVisual() {
  return (
    <div className="relative w-full">
      {/* ambient glow */}
      <div className="pointer-events-none absolute -inset-x-10 -top-10 bottom-0 -z-10">
        <div className="absolute left-1/2 top-1/3 h-72 w-72 -translate-x-1/2 rounded-full bg-[var(--accent-glow)] blur-[100px]" />
      </div>

      <div className="overflow-hidden rounded-2xl border border-border-subtle bg-surface shadow-2xl shadow-black/20">
        {/* window chrome */}
        <div className="flex items-center gap-2 border-b border-border-subtle bg-surface-2/60 px-4 py-3">
          <span className="h-3 w-3 rounded-full bg-zinc-300 dark:bg-zinc-700" />
          <span className="h-3 w-3 rounded-full bg-zinc-300 dark:bg-zinc-700" />
          <span className="h-3 w-3 rounded-full bg-zinc-300 dark:bg-zinc-700" />
          <div className="ml-3 flex items-center gap-1.5 rounded-md bg-surface px-2.5 py-1 text-[11px] font-medium text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
            omni-rag.app/workspace
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-[180px_1fr]">
          {/* sources rail */}
          <div className="hidden flex-col gap-1.5 border-r border-border-subtle bg-surface-2/30 p-3 sm:flex">
            <p className="px-1 pb-1 text-[10px] font-semibold uppercase tracking-wider text-muted">
              Sources
            </p>
            {sources.map((s) => (
              <div
                key={s.name}
                className={`flex items-center gap-2 rounded-lg px-2 py-2 text-xs ${
                  s.active
                    ? "bg-accent-soft text-foreground"
                    : "text-muted"
                }`}
              >
                <s.icon
                  className={`h-3.5 w-3.5 shrink-0 ${s.active ? "text-accent" : ""}`}
                />
                <div className="min-w-0">
                  <p className="truncate font-medium">{s.name}</p>
                  <p className="text-[10px] text-muted">{s.meta}</p>
                </div>
              </div>
            ))}
          </div>

          {/* chat */}
          <div className="flex flex-col gap-4 p-4 sm:p-5">
            {/* user question */}
            <div className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-br-md bg-foreground px-3.5 py-2.5 text-[13px] font-medium text-background">
                What drove our Q4 revenue growth?
              </div>
            </div>

            {/* answer */}
            <div className="flex gap-2.5">
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-accent-soft">
                <Sparkles className="h-3.5 w-3.5 text-accent" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="rounded-2xl rounded-tl-md border border-border-subtle bg-surface-2/50 p-3.5">
                  <p className="text-[13px] leading-relaxed text-foreground">
                    Q4 revenue grew{" "}
                    <span className="font-semibold text-accent">31% year over year</span>{" "}
                    to $48.2M, led by enterprise renewals and expansion in existing
                    accounts
                    <motion.span
                      animate={{ opacity: [1, 1, 0, 0] }}
                      transition={{ duration: 1, repeat: Infinity, times: [0, 0.5, 0.5, 1] }}
                      className="ml-0.5 inline-block h-3.5 w-[2px] translate-y-0.5 bg-accent"
                    />
                  </p>

                  {/* citations */}
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {[
                      { label: "Report · p.12", icon: FileText },
                      { label: "Report · p.14", icon: FileText },
                      { label: "Call · 12:04", icon: Video },
                    ].map((c) => (
                      <span
                        key={c.label}
                        className="inline-flex items-center gap-1 rounded-md border border-border-subtle bg-surface px-2 py-1 text-[10px] font-medium text-muted"
                      >
                        <c.icon className="h-3 w-3 text-accent" />
                        {c.label}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* floating citation chip */}
      <motion.div
        animate={{ y: [0, -10, 0] }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
        className="absolute -bottom-6 right-4 hidden rounded-xl border border-border-subtle bg-surface p-3 shadow-xl sm:right-8 sm:block lg:-right-5 lg:bottom-10"
      >
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent-soft">
            <Quote className="h-3.5 w-3.5 text-accent" />
          </div>
          <div>
            <p className="text-[11px] font-semibold text-foreground">Verified source</p>
            <p className="text-[10px] text-muted">Annual_Report.pdf, page 12</p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
