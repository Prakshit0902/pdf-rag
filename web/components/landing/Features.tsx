"use client";

import React from "react";
import { Check } from "lucide-react";
import SectionHeading from "./SectionHeading";
import Reveal from "./Reveal";
import FeatureVisual from "./FeatureVisual";
import { features } from "@/lib/landing-content";

export default function Features() {
  return (
    <section id="features" className="relative px-4 py-24 sm:px-6 sm:py-32">
      <div className="mx-auto max-w-6xl">
        <SectionHeading
          eyebrow="Features"
          title="Built so you can trust the answer"
          description="The hard parts of reading, searching, and citing happen behind the scenes. You just ask."
        />

        <div className="mt-20 space-y-24 sm:space-y-32">
          {features.map((feature, i) => {
            const flipped = i % 2 === 1;
            return (
              <div
                key={feature.id}
                className="grid items-center gap-10 lg:grid-cols-2 lg:gap-16"
              >
                <Reveal
                  direction={flipped ? "left" : "right"}
                  className={flipped ? "lg:order-2" : ""}
                >
                  <span className="text-xs font-semibold uppercase tracking-wider text-accent">
                    {feature.eyebrow}
                  </span>
                  <h3 className="mt-3 text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
                    {feature.title}
                  </h3>
                  <p className="mt-4 text-base leading-relaxed text-muted">
                    {feature.description}
                  </p>
                  <ul className="mt-6 space-y-3">
                    {feature.bullets.map((bullet) => (
                      <li key={bullet} className="flex items-start gap-3">
                        <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent-soft">
                          <Check className="h-3 w-3 text-accent" />
                        </span>
                        <span className="text-sm font-medium text-foreground">
                          {bullet}
                        </span>
                      </li>
                    ))}
                  </ul>
                </Reveal>

                <Reveal
                  direction={flipped ? "right" : "left"}
                  delay={0.1}
                  className={flipped ? "lg:order-1" : ""}
                >
                  <FeatureVisual visual={feature.visual} />
                </Reveal>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
