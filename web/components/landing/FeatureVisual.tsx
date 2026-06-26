"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Video,
  Presentation,
  FileType2,
  Search,
  ShieldCheck,
  Lock,
  Sparkles,
} from "lucide-react";
import type { Feature } from "@/lib/landing-content";

const cardBase =
  "relative aspect-[4/3] w-full overflow-hidden rounded-2xl border border-border-subtle bg-surface-2/40 p-5 sm:p-7";

function AnswerVisual() {
  return (
    <div className={cardBase}>
      <div className="absolute inset-0 bg-dots opacity-50" />
      <div className="relative flex h-full flex-col justify-center">
        <div className="rounded-2xl border border-border-subtle bg-surface p-4 shadow-lg">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent-soft">
              <Sparkles className="h-3 w-3 text-accent" />
            </span>
            <span className="text-xs font-semibold text-foreground">Answer</span>
          </div>
          <div className="mt-3 space-y-2">
            <div className="h-2 w-full rounded-full bg-surface-2" />
            <div className="h-2 w-[88%] rounded-full bg-surface-2" />
            <div className="h-2 w-[64%] rounded-full bg-surface-2" />
          </div>
          <div className="mt-4 flex flex-wrap gap-1.5">
            {[
              { label: "p.12", icon: FileText },
              { label: "p.14", icon: FileText },
              { label: "12:04", icon: Video },
            ].map((c, i) => (
              <motion.span
                key={c.label}
                initial={{ opacity: 0, scale: 0.85 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 + i * 0.12 }}
                className="inline-flex items-center gap-1 rounded-md border border-accent/30 bg-accent-soft px-2 py-1 text-[10px] font-semibold text-accent"
              >
                <c.icon className="h-3 w-3" />
                {c.label}
              </motion.span>
            ))}
          </div>
        </div>
        <p className="mt-3 text-center text-[11px] text-muted">
          Hover a citation to jump to the exact source
        </p>
      </div>
    </div>
  );
}

function SearchVisual() {
  const rows = [
    { label: "revenue growth", kind: "meaning", w: "92%" },
    { label: "\u201cclause 7.2\u201d", kind: "exact", w: "84%" },
    { label: "EU expansion", kind: "meaning", w: "73%" },
    { label: "SKU-4192", kind: "exact", w: "68%" },
  ];
  return (
    <div className={cardBase}>
      <div className="relative flex h-full flex-col justify-center gap-3">
        <div className="flex items-center gap-2 rounded-xl border border-border-subtle bg-surface px-3 py-2.5">
          <Search className="h-4 w-4 text-accent" />
          <span className="text-xs text-muted">What drove EU revenue in clause 7.2?</span>
        </div>
        <div className="space-y-2.5">
          {rows.map((r, i) => (
            <motion.div
              key={r.label}
              initial={{ opacity: 0, x: -12 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="flex items-center gap-2"
            >
              <span
                className={`w-14 shrink-0 text-[9px] font-semibold uppercase tracking-wide ${
                  r.kind === "meaning" ? "text-accent" : "text-emerald-500"
                }`}
              >
                {r.kind}
              </span>
              <div className="relative h-6 flex-1 overflow-hidden rounded-md bg-surface">
                <motion.div
                  initial={{ width: 0 }}
                  whileInView={{ width: r.w }}
                  viewport={{ once: true }}
                  transition={{ delay: 0.15 + i * 0.1, duration: 0.7, ease: "easeOut" }}
                  className={`h-full rounded-md ${
                    r.kind === "meaning" ? "bg-accent/25" : "bg-emerald-500/25"
                  }`}
                />
                <span className="absolute inset-0 flex items-center px-2 text-[10px] font-medium text-foreground">
                  {r.label}
                </span>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FormatsVisual() {
  const tiles = [
    { icon: FileText, label: "PDF" },
    { icon: FileType2, label: "DOCX" },
    { icon: Presentation, label: "PPTX" },
    { icon: Video, label: "Video" },
  ];
  return (
    <div className={cardBase}>
      <div className="relative flex h-full items-center justify-center">
        <div className="grid grid-cols-2 gap-3">
          {tiles.map((t, i) => (
            <motion.div
              key={t.label}
              initial={{ opacity: 0, y: 14 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              whileHover={{ y: -4 }}
              className="flex h-24 w-28 flex-col items-center justify-center gap-2 rounded-xl border border-border-subtle bg-surface"
            >
              <t.icon className="h-6 w-6 text-accent" />
              <span className="text-[11px] font-semibold text-foreground">{t.label}</span>
            </motion.div>
          ))}
        </div>
        {/* center node */}
        <motion.div
          initial={{ scale: 0 }}
          whileInView={{ scale: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.45, type: "spring", bounce: 0.4 }}
          className="absolute flex h-14 w-14 items-center justify-center rounded-full border border-accent/40 bg-surface shadow-lg"
        >
          <Sparkles className="h-5 w-5 text-accent" />
        </motion.div>
      </div>
    </div>
  );
}

function PrivacyVisual() {
  return (
    <div className={cardBase}>
      <div className="absolute inset-0 bg-grid opacity-40" />
      <div className="relative flex h-full flex-col items-center justify-center gap-4">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          whileInView={{ scale: 1, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ type: "spring", bounce: 0.35 }}
          className="relative flex h-20 w-20 items-center justify-center rounded-2xl border border-border-subtle bg-surface shadow-xl"
        >
          <ShieldCheck className="h-9 w-9 text-accent" />
          <span className="absolute -right-1.5 -top-1.5 flex h-6 w-6 items-center justify-center rounded-full border border-border-subtle bg-surface">
            <Lock className="h-3 w-3 text-foreground" />
          </span>
        </motion.div>
        <div className="flex flex-col items-center gap-1.5">
          {["Your files", "Your conversations", "Your account only"].map((t, i) => (
            <motion.span
              key={t}
              initial={{ opacity: 0, y: 8 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 + i * 0.1 }}
              className="rounded-full border border-border-subtle bg-surface px-3 py-1 text-[11px] font-medium text-muted"
            >
              {t}
            </motion.span>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function FeatureVisual({ visual }: { visual: Feature["visual"] }) {
  switch (visual) {
    case "answer":
      return <AnswerVisual />;
    case "search":
      return <SearchVisual />;
    case "formats":
      return <FormatsVisual />;
    case "privacy":
      return <PrivacyVisual />;
    default:
      return null;
  }
}
