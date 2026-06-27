"use client";

import React from "react";
import ChatInterface from "@/components/ChatInterface";
import ThemeToggle from "@/components/ThemeToggle";
import Logo from "@/components/landing/Logo";
import Link from "next/link";
import { UserButton } from "@clerk/nextjs";
import { brand } from "@/lib/landing-content";

export default function WorkspacePage() {
  return (
    <div className="flex flex-col h-screen w-full bg-background font-sans text-foreground">
      <header className="flex-none h-14 border-b border-border-subtle bg-surface/80 backdrop-blur-xl z-50 flex items-center justify-between px-4 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5 hover:opacity-90 transition-opacity">
          <Logo size={28} className="transition-transform group-hover:scale-105" />
          <span className="text-[17px] font-semibold tracking-tight text-foreground">{brand.name}</span>
        </Link>
        <div className="flex items-center gap-3 sm:gap-4">
          <ThemeToggle />
          <UserButton
            appearance={{
              elements: { avatarBox: "h-8 w-8 ring-2 ring-border-subtle" },
            }}
          />
        </div>
      </header>
      <main className="flex-1 overflow-hidden relative">
        <ChatInterface />
      </main>
    </div>
  );
}
