"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Determine initial theme on client mount
    const isDark = document.documentElement.classList.contains("dark");
    setTheme(isDark ? "dark" : "light");
    setMounted(true);
  }, []);

  const toggleTheme = () => {
    if (theme === "dark") {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
      setTheme("light");
    } else {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
      setTheme("dark");
    }
  };

  if (!mounted) {
    return (
      <div className="w-9 h-9 rounded-xl border border-border-subtle bg-surface" />
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-xl border border-border-subtle bg-surface hover:bg-surface-2 text-foreground transition-colors cursor-pointer shadow-sm relative overflow-hidden focus:outline-none"
      aria-label="Toggle theme"
    >
      <div className="w-5 h-5 flex items-center justify-center relative overflow-hidden">
        <AnimatePresence mode="wait" initial={false}>
          {theme === "dark" ? (
            <motion.div
              key="sun"
              initial={{ y: 20, rotate: 90, opacity: 0 }}
              animate={{ y: 0, rotate: 0, opacity: 1 }}
              exit={{ y: -20, rotate: -90, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              <Sun className="w-5 h-5 text-accent" />
            </motion.div>
          ) : (
            <motion.div
              key="moon"
              initial={{ y: 20, rotate: 90, opacity: 0 }}
              animate={{ y: 0, rotate: 0, opacity: 1 }}
              exit={{ y: -20, rotate: -90, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              <Moon className="w-5 h-5 text-accent" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </button>
  );
}
