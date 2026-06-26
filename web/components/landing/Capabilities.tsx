"use client";

import React from "react";
import { Stagger, StaggerItem } from "./Reveal";
import { capabilities } from "@/lib/landing-content";

export default function Capabilities() {
  return (
    <section className="px-4 sm:px-6">
      <div className="mx-auto max-w-6xl">
        <Stagger className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-border-subtle bg-border-subtle lg:grid-cols-4">
          {capabilities.map((cap) => (
            <StaggerItem key={cap.label}>
              <div className="flex h-full flex-col gap-3 bg-surface p-6 sm:p-8">
                <cap.icon className="h-5 w-5 text-accent" />
                <p className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                  {cap.value}
                </p>
                <p className="text-sm leading-snug text-muted">{cap.label}</p>
              </div>
            </StaggerItem>
          ))}
        </Stagger>
      </div>
    </section>
  );
}
