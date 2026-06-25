"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { UserButton, SignInButton, useUser } from "@clerk/nextjs";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Menu, X } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import Logo from "./Logo";
import { brand, nav } from "@/lib/landing-content";

export default function Navbar() {
  const { isSignedIn, isLoaded } = useUser();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.21, 0.47, 0.32, 0.98] }}
      className="fixed top-0 inset-x-0 z-50"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div
          className={`mt-3 flex h-14 items-center justify-between rounded-2xl border px-3 sm:px-4 transition-all duration-300 ${
            scrolled
              ? "border-border-subtle bg-surface/80 shadow-lg shadow-black/5 backdrop-blur-xl"
              : "border-transparent bg-transparent"
          }`}
        >
          <Link href="/" className="group flex items-center gap-2.5">
            <Logo size={30} className="transition-transform group-hover:scale-105" />
            <span className="text-[17px] font-semibold tracking-tight text-foreground">
              {brand.name}
            </span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            {nav.links.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2 text-sm font-medium text-muted transition-colors hover:text-foreground"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2 sm:gap-3">
            <ThemeToggle />

            {isLoaded && isSignedIn ? (
              <div className="flex items-center gap-3">
                <Link
                  href="/workspace"
                  className="hidden items-center gap-1.5 rounded-full bg-foreground px-4 py-2 text-sm font-semibold text-background transition-opacity hover:opacity-90 sm:flex"
                >
                  Workspace <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <UserButton
                  appearance={{
                    elements: { avatarBox: "h-8 w-8 ring-2 ring-border-subtle" },
                  }}
                />
              </div>
            ) : (
              <div className="flex items-center gap-2 sm:gap-3">
                <SignInButton mode="modal">
                  <button className="hidden text-sm font-medium text-muted transition-colors hover:text-foreground sm:block">
                    Sign in
                  </button>
                </SignInButton>
                <Link
                  href="/workspace"
                  className="flex items-center gap-1.5 rounded-full bg-foreground px-4 py-2 text-sm font-semibold text-background transition-all hover:opacity-90"
                >
                  Get started
                </Link>
              </div>
            )}

            <button
              onClick={() => setOpen((v) => !v)}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-border-subtle text-foreground md:hidden"
              aria-label="Toggle menu"
            >
              {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <AnimatePresence>
          {open && (
            <motion.nav
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="mt-2 overflow-hidden rounded-2xl border border-border-subtle bg-surface/95 p-2 shadow-xl backdrop-blur-xl md:hidden"
            >
              {nav.links.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="block rounded-lg px-3 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-surface-2"
                >
                  {link.label}
                </a>
              ))}
            </motion.nav>
          )}
        </AnimatePresence>
      </div>
    </motion.header>
  );
}
