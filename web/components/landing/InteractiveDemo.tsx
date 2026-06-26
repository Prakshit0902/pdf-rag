"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  AnimatePresence,
  motion,
  useInView,
  useReducedMotion,
} from "framer-motion";
import {
  FileText,
  Video,
  Search,
  Sparkles,
  RotateCcw,
  CornerDownLeft,
  Loader2,
} from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import { demo } from "@/lib/landing-content";

type Phase = "idle" | "typing" | "searching" | "answering" | "done";

type Segment = { text: string; bold: boolean };

function parseBold(input: string): Segment[] {
  return input.split("**").map((text, i) => ({ text, bold: i % 2 === 1 }));
}

const sourceIcons = [FileText, FileText, Video];

export default function InteractiveDemo() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { margin: "-120px" });
  const reduce = useReducedMotion();

  const [phase, setPhase] = useState<Phase>("idle");
  const [typed, setTyped] = useState(0);
  const [sourceCount, setSourceCount] = useState(0);
  const [answerLen, setAnswerLen] = useState(0);
  const [cited, setCited] = useState(false);
  const [replayKey, setReplayKey] = useState(0);

  const runRef = useRef(0);

  const segments = useMemo(() => parseBold(demo.answer), []);
  const plain = useMemo(() => segments.map((s) => s.text).join(""), [segments]);
  const question = demo.question;

  useEffect(() => {
    if (!inView) return;

    if (reduce) {
      setTyped(question.length);
      setSourceCount(demo.sources.length);
      setAnswerLen(plain.length);
      setCited(true);
      setPhase("done");
      return;
    }

    const id = ++runRef.current;
    let cancelled = false;
    const alive = () => !cancelled && id === runRef.current;
    const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

    async function run() {
      setPhase("idle");
      setTyped(0);
      setSourceCount(0);
      setAnswerLen(0);
      setCited(false);
      await sleep(450);
      if (!alive()) return;

      setPhase("typing");
      for (let i = 1; i <= question.length; i++) {
        if (!alive()) return;
        setTyped(i);
        await sleep(26);
      }
      await sleep(350);
      if (!alive()) return;

      setPhase("searching");
      for (let i = 1; i <= demo.sources.length; i++) {
        if (!alive()) return;
        setSourceCount(i);
        await sleep(430);
      }
      await sleep(300);
      if (!alive()) return;

      setPhase("answering");
      for (let i = 1; i <= plain.length; i++) {
        if (!alive()) return;
        setAnswerLen(i);
        await sleep(13);
      }
      if (!alive()) return;
      setCited(true);
      setPhase("done");
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [inView, replayKey, reduce, question, plain]);

  const statusLabel =
    phase === "typing"
      ? "Reading your question"
      : phase === "searching"
      ? "Searching your sources"
      : phase === "answering"
      ? "Writing the answer"
      : phase === "done"
      ? "Answer ready"
      : "Ready";

  let remaining = answerLen;

  return (
    <section id="demo" className="relative px-4 py-24 sm:px-6 sm:py-32">
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute left-1/2 top-1/2 h-[420px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--accent-glow)] opacity-50 blur-[150px]" />
      </div>

      <div className="mx-auto max-w-5xl">
        <SectionHeading
          eyebrow="Live demo"
          title="Watch a question become a cited answer"
          description="This runs on its own. Hit replay any time to see the whole flow again."
        />

        <Reveal className="mt-14">
          <div
            ref={ref}
            className="overflow-hidden rounded-3xl border border-border-subtle bg-surface shadow-2xl shadow-black/10"
          >
            {/* status bar */}
            <div className="flex items-center justify-between border-b border-border-subtle bg-surface-2/50 px-5 py-3">
              <div className="flex items-center gap-2.5">
                {phase === "searching" || phase === "answering" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />
                ) : (
                  <span className="flex h-2 w-2 rounded-full bg-accent" />
                )}
                <span className="text-xs font-medium text-muted">{statusLabel}</span>
              </div>
              <button
                onClick={() => setReplayKey((k) => k + 1)}
                className="inline-flex items-center gap-1.5 rounded-full border border-border-subtle bg-surface px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-surface-2"
              >
                <RotateCcw className="h-3 w-3" />
                Replay
              </button>
            </div>

            <div className="grid gap-0 lg:grid-cols-[1fr_320px]">
              {/* main conversation */}
              <div className="flex flex-col gap-5 p-5 sm:p-7">
                {/* question input */}
                <div className="flex items-center gap-3 rounded-xl border border-border-subtle bg-surface-2/40 px-4 py-3">
                  <Search className="h-4 w-4 shrink-0 text-muted" />
                  <span className="text-sm text-foreground">
                    {question.slice(0, typed)}
                    {phase === "typing" && (
                      <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-caret bg-accent align-middle" />
                    )}
                  </span>
                  {phase !== "idle" && phase !== "typing" && (
                    <CornerDownLeft className="ml-auto h-3.5 w-3.5 shrink-0 text-muted" />
                  )}
                </div>

                {/* answer */}
                <AnimatePresence>
                  {(phase === "answering" || phase === "done") && (
                    <motion.div
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex gap-3"
                    >
                      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-soft">
                        <Sparkles className="h-4 w-4 text-accent" />
                      </span>
                      <div className="min-w-0 flex-1 rounded-2xl rounded-tl-md border border-border-subtle bg-surface-2/40 p-4">
                        <p className="text-sm leading-relaxed text-foreground">
                          {segments.map((seg, i) => {
                            const show = Math.max(
                              0,
                              Math.min(seg.text.length, remaining)
                            );
                            remaining -= seg.text.length;
                            const visible = seg.text.slice(0, show);
                            if (!visible) return null;
                            return (
                              <span
                                key={i}
                                className={
                                  seg.bold ? "font-semibold text-accent" : ""
                                }
                              >
                                {visible}
                              </span>
                            );
                          })}
                          {phase === "answering" && (
                            <span className="ml-0.5 inline-block h-4 w-[2px] translate-y-0.5 animate-caret bg-accent align-middle" />
                          )}
                        </p>

                        <AnimatePresence>
                          {cited && (
                            <motion.div
                              initial={{ opacity: 0, y: 8 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="mt-4 flex flex-wrap gap-1.5 border-t border-border-subtle pt-3"
                            >
                              <span className="mr-1 text-[11px] font-medium text-muted">
                                Sources:
                              </span>
                              {demo.citations.map((c, i) => (
                                <motion.span
                                  key={c}
                                  initial={{ opacity: 0, scale: 0.85 }}
                                  animate={{ opacity: 1, scale: 1 }}
                                  transition={{ delay: i * 0.1 }}
                                  className="inline-flex items-center gap-1 rounded-md border border-accent/30 bg-accent-soft px-2 py-1 text-[10px] font-semibold text-accent"
                                >
                                  {c}
                                </motion.span>
                              ))}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* sources rail */}
              <div className="border-t border-border-subtle bg-surface-2/30 p-5 sm:p-6 lg:border-l lg:border-t-0">
                <p className="mb-3 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
                  <Search className="h-3.5 w-3.5" />
                  Retrieved passages
                </p>
                <div className="space-y-2.5">
                  {demo.sources.map((src, i) => {
                    const Icon = sourceIcons[i] ?? FileText;
                    const shown = i < sourceCount;
                    return (
                      <motion.div
                        key={src.tag}
                        animate={{
                          opacity: shown ? 1 : 0.25,
                          y: shown ? 0 : 6,
                        }}
                        transition={{ duration: 0.35 }}
                        className={`rounded-xl border p-3 ${
                          shown
                            ? "border-accent/30 bg-surface"
                            : "border-border-subtle bg-surface/40"
                        }`}
                      >
                        <div className="flex items-center gap-1.5">
                          <Icon className="h-3 w-3 text-accent" />
                          <span className="text-[10px] font-semibold text-muted">
                            {src.tag}
                          </span>
                        </div>
                        <p className="mt-1.5 text-xs leading-snug text-foreground">
                          {src.text}
                        </p>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
