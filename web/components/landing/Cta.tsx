"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import Reveal from "./Reveal";
import { finalCta } from "@/lib/landing-content";

export default function Cta() {
  return (
    <section className="px-4 py-20 sm:px-6 sm:py-28">
      <Reveal className="mx-auto max-w-5xl">
        <div className="relative overflow-hidden rounded-[2rem] border border-border-subtle bg-zinc-950 px-6 py-16 text-center sm:px-12 sm:py-24 dark:bg-surface-2">
          {/* texture */}
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute inset-0 bg-grid opacity-[0.07]" />
            <div className="absolute left-1/2 top-1/2 h-[400px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--accent-glow)] opacity-60 blur-[120px]" />
          </div>

          <div className="relative">
            <span className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-3.5 py-1.5 text-xs font-medium text-zinc-300">
              <span className="h-1.5 w-1.5 rounded-full bg-accent" />
              {finalCta.badge}
            </span>
            <h2 className="mx-auto mt-6 max-w-2xl text-balance text-3xl font-semibold tracking-tight text-white sm:text-5xl">
              {finalCta.title}
            </h2>
            <p className="mx-auto mt-5 max-w-xl text-pretty text-base leading-relaxed text-zinc-400 sm:text-lg">
              {finalCta.subtitle}
            </p>
            <div className="mt-9 flex justify-center">
              <Link
                href="/workspace"
                className="group inline-flex items-center justify-center gap-2 rounded-full bg-white px-8 py-4 text-sm font-semibold text-zinc-900 transition-transform hover:scale-[1.03]"
              >
                {finalCta.primary}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>
          </div>
        </div>
      </Reveal>
    </section>
  );
}
