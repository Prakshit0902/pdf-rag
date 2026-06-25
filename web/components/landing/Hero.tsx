"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  AnimatePresence,
  motion,
  useReducedMotion,
  useScroll,
  useTransform,
} from "framer-motion";
import { ArrowRight, Play } from "lucide-react";
import ProductVisual from "./ProductVisual";
import { hero } from "@/lib/landing-content";

export default function Hero() {
  const ref = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], [0, reduce ? 0 : 120]);
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, reduce ? 1 : 0]);

  const [wordIndex, setWordIndex] = useState(0);
  useEffect(() => {
    if (reduce) return;
    const id = setInterval(
      () => setWordIndex((i) => (i + 1) % hero.titleRotators.length),
      2200
    );
    return () => clearInterval(id);
  }, [reduce]);

  const ease = [0.21, 0.47, 0.32, 0.98] as const;

  return (
    <section
      ref={ref}
      className="relative overflow-hidden px-4 pb-16 pt-32 sm:px-6 sm:pt-40 lg:pt-44"
    >
      {/* backdrop */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-grid mask-fade-b opacity-60" />
        <div className="absolute left-1/2 top-0 h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-[var(--accent-glow)] blur-[140px] opacity-70" />
      </div>

      <motion.div style={{ y, opacity }} className="mx-auto max-w-3xl text-center">
        <motion.a
          href="#features"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease }}
          className="group inline-flex items-center gap-2 rounded-full border border-border-subtle bg-surface/70 px-3.5 py-1.5 text-xs font-medium text-muted backdrop-blur-sm transition-colors hover:text-foreground"
        >
          <span className="flex h-1.5 w-1.5">
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-accent" />
          </span>
          {hero.eyebrow}
          <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5" />
        </motion.a>

        <motion.h1
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.08, ease }}
          className="mt-6 text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-foreground sm:text-6xl lg:text-7xl"
        >
          {hero.titleLead}
          <br className="hidden sm:block" />{" "}
          <span className="relative inline-flex min-w-[4ch] justify-center">
            <AnimatePresence mode="wait">
              <motion.span
                key={wordIndex}
                initial={{ opacity: 0, y: "0.5em", filter: "blur(4px)" }}
                animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                exit={{ opacity: 0, y: "-0.5em", filter: "blur(4px)" }}
                transition={{ duration: 0.45, ease }}
                className="bg-gradient-to-r from-accent to-accent-strong bg-clip-text text-transparent"
              >
                {hero.titleRotators[wordIndex]}
              </motion.span>
            </AnimatePresence>
          </span>
          <br />
          {hero.titleTail}
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.18, ease }}
          className="mx-auto mt-6 max-w-2xl text-pretty text-base leading-relaxed text-muted sm:text-lg"
        >
          {hero.subtitle}
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 22 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.28, ease }}
          className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row"
        >
          <Link
            href="/workspace"
            className="group inline-flex w-full items-center justify-center gap-2 rounded-full bg-foreground px-7 py-3.5 text-sm font-semibold text-background shadow-lg shadow-black/10 transition-all hover:scale-[1.02] sm:w-auto"
          >
            {hero.primaryCta}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <a
            href="#demo"
            className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-border-subtle bg-surface px-7 py-3.5 text-sm font-semibold text-foreground transition-colors hover:bg-surface-2 sm:w-auto"
          >
            <Play className="h-3.5 w-3.5 fill-current" />
            {hero.secondaryCta}
          </a>
        </motion.div>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.4, ease }}
          className="mt-5 text-xs text-muted"
        >
          {hero.footnote}
        </motion.p>
      </motion.div>

      {/* product preview */}
      <motion.div
        initial={{ opacity: 0, y: 48, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.9, delay: 0.35, ease }}
        className="mx-auto mt-16 max-w-4xl px-1 sm:mt-20"
      >
        <ProductVisual />
      </motion.div>
    </section>
  );
}
