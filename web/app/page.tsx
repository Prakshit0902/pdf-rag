import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import FileUpload from "@/components/FileUpload";
import ChatInterface from "@/components/ChatInterface";
import { Show, SignInButton, UserButton } from "@clerk/nextjs";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Premium PDF RAG Workspace",
  description: "Secure, tenant-isolated PDF intelligence platform",
};

export default function Home() {
  return (
    <div className={`${geistSans.variable} min-h-screen bg-zinc-950 text-zinc-100 font-sans flex flex-col selection:bg-indigo-500 selection:text-white`}>
      {/* Background radial glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-indigo-950/30 via-zinc-950 to-zinc-950 pointer-events-none z-0" />

      {/* SIGNED OUT: Landing Page */}
      <Show when="signed-out">
        <div className="flex-1 flex flex-col items-center justify-center p-6 relative z-10">
          <div className="max-w-xl w-full text-center space-y-8">
            <div className="space-y-4">
              <span className="px-3 py-1 text-xs font-semibold tracking-wider text-indigo-400 bg-indigo-950/50 border border-indigo-900 rounded-full inline-block">
                SaaS Enterprise Edition
              </span>
              <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-zinc-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
                PDF Intelligence.
                <span className="block mt-1 bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text">
                  Isolated. Scoped. Secure.
                </span>
              </h1>
              <p className="text-zinc-400 text-lg sm:text-xl max-w-lg mx-auto font-light">
                Analyze and query private documents with complete data separation. Powered by Qdrant Vector Search, BM25 Hybrid Retrieval, and Gemini.
              </p>
            </div>

            <div className="flex justify-center gap-4">
              <SignInButton mode="modal">
                <button className="relative group overflow-hidden px-8 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 text-white font-semibold shadow-[0_0_20px_rgba(99,102,241,0.3)] hover:shadow-[0_0_30px_rgba(99,102,241,0.5)] transition-all duration-300 transform hover:-translate-y-0.5 cursor-pointer">
                  <span className="relative z-10">Access Workspace</span>
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                </button>
              </SignInButton>
            </div>

            <div className="grid grid-cols-3 gap-6 pt-12 border-t border-zinc-900 max-w-md mx-auto text-sm text-zinc-500 font-medium">
              <div>
                <p className="text-zinc-300 text-base font-semibold">100%</p>
                <p className="text-xs mt-1">Tenant Isolated</p>
              </div>
              <div className="border-x border-zinc-900">
                <p className="text-zinc-300 text-base font-semibold">Qdrant + BM25</p>
                <p className="text-xs mt-1">Hybrid Retrieval</p>
              </div>
              <div>
                <p className="text-zinc-300 text-base font-semibold">Persistent</p>
                <p className="text-xs mt-1">Supabase Memory</p>
              </div>
            </div>
          </div>
        </div>
      </Show>

      {/* SIGNED IN: Application Workspace */}
      <Show when="signed-in">
        <header className="bg-zinc-900/60 backdrop-blur-md border-b border-zinc-800/80 sticky top-0 py-4 px-6 flex items-center justify-between z-50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center font-bold text-white shadow-md">
              Ω
            </div>
            <div>
              <h1 className="text-base font-bold text-zinc-100 leading-none">PDF RAG</h1>
              <p className="text-[10px] text-zinc-500 mt-1 font-medium tracking-wide uppercase">Workspace Console</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="px-2 py-0.5 rounded text-[11px] font-semibold text-emerald-400 bg-emerald-950/40 border border-emerald-900/50 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Connected
            </span>
            <UserButton
              appearance={{
                elements: {
                  avatarBox: "w-9 h-9 border border-zinc-700/50 hover:border-zinc-500 transition-colors",
                },
              }}
            />
          </div>
        </header>

        <main className="flex-1 max-w-6xl w-full mx-auto py-10 px-6 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-5 space-y-8">
              <div className="bg-zinc-900/30 border border-zinc-800/60 p-6 rounded-2xl">
                <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-2">Workspace Isolation</h3>
                <p className="text-zinc-500 text-xs leading-relaxed">
                  Your document cache, vector representations, indexes, and chat memories are isolated inside your personal Clerk Tenant ID. Other users cannot search, view, or process your files.
                </p>
              </div>
              <FileUpload />
            </div>
            <div className="lg:col-span-7">
              <ChatInterface />
            </div>
          </div>
        </main>
      </Show>

      {/* Tiny footer */}
      <footer className="py-4 border-t border-zinc-950 text-center text-[11px] text-zinc-600 relative z-10 font-medium">
        Isolated PDF RAG Workspace &copy; {new Date().getFullYear()} — Built with Clerk & Supabase
      </footer>
    </div>
  );
}