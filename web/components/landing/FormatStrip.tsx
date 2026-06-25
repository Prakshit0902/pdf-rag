"use client";

import React from "react";
import { formats } from "@/lib/landing-content";

export default function FormatStrip() {
  const items = [...formats, ...formats, ...formats];

  return (
    <section className="border-y border-border-subtle bg-surface/40 py-10">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <p className="mb-7 text-center text-xs font-medium uppercase tracking-[0.18em] text-muted">
          Bring in what you already have
        </p>
        <div className="group relative overflow-hidden mask-fade-x">
          <div className="flex w-max gap-3 animate-marquee [--duration:32s] group-hover:[animation-play-state:paused]">
            {items.map((f, i) => (
              <div
                key={`${f.ext}-${i}`}
                className="flex shrink-0 items-center gap-2.5 rounded-xl border border-border-subtle bg-surface px-4 py-3"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent-soft">
                  <f.icon className="h-4 w-4 text-accent" />
                </span>
                <span className="text-sm font-medium text-foreground">{f.label}</span>
                <span className="rounded-md bg-surface-2 px-1.5 py-0.5 text-[10px] font-semibold tracking-wide text-muted">
                  {f.ext}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
