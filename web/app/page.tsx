import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import FileUpload from "@/components/FileUpload";
import ChatInterface from "@/components/ChatInterface";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PDF RAG",
  description: "Upload PDFs and chat with them",
};

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 font-sans">
      <header className="bg-white border-b border-zinc-200 py-4 px-6">
        <h1 className="text-xl font-semibold text-zinc-800">PDF RAG System</h1>
      </header>

      <main className="max-w-5xl mx-auto py-12 px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <FileUpload />
          <ChatInterface />
        </div>
      </main>
    </div>
  );
}