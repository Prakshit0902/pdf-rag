import React from "react";
import Navbar from "@/components/landing/Navbar";
import Hero from "@/components/landing/Hero";
import FormatStrip from "@/components/landing/FormatStrip";
import HowItWorks from "@/components/landing/HowItWorks";
import Features from "@/components/landing/Features";
import InteractiveDemo from "@/components/landing/InteractiveDemo";
import Capabilities from "@/components/landing/Capabilities";
import Faq from "@/components/landing/Faq";
import Cta from "@/components/landing/Cta";
import Footer from "@/components/landing/Footer";

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-background font-sans text-foreground selection:bg-accent-soft">
      <Navbar />
      <main>
        <Hero />
        <FormatStrip />
        <HowItWorks />
        <Features />
        <InteractiveDemo />
        <Capabilities />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </div>
  );
}
