"use client";

import React from "react";
import SectionHeading from "./SectionHeading";
import { Stagger, StaggerItem } from "./Reveal";
import { steps } from "@/lib/landing-content";

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="relative px-4 py-24 sm:px-6 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          eyebrow="How it works"
          title="From a pile of files to an answer in three steps"
          description="No setup, no training, no learning curve. If you can ask a question, you can use it."
        />

        <Stagger className="relative mt-16 grid gap-6 md:grid-cols-3">
          {/* connector line */}
          <div className="pointer-events-none absolute left-0 right-0 top-[2.85rem] hidden h-px bg-gradient-to-r from-transparent via-border-subtle to-transparent md:block" />

          {steps.map((step) => (
            <StaggerItem key={step.index}>
              <div className="group relative h-full rounded-2xl border border-border-subtle bg-surface p-6 transition-colors hover:border-accent/40">
                <div className="flex items-center justify-between">
                  <span className="flex h-12 w-12 items-center justify-center rounded-xl border border-border-subtle bg-surface-2 text-accent transition-colors group-hover:bg-accent-soft">
                    <step.icon className="h-5 w-5" />
                  </span>
                  <span className="font-mono text-sm font-semibold text-muted/60">
                    {step.index}
                  </span>
                </div>
                <h3 className="mt-5 text-lg font-semibold text-foreground">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted">
                  {step.description}
                </p>
              </div>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  );
}
