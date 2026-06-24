"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { UserButton, SignInButton, useUser } from "@clerk/nextjs";
import { motion, useScroll, useTransform } from "framer-motion";
import ThemeToggle from "@/components/ThemeToggle";
import { 
  Database, 
  BrainCircuit, 
  ShieldCheck, 
  Zap, 
  Files,
  Play,
  ArrowRight,
  Cpu,
  Layers,
  Sparkles
} from "lucide-react";

// Components
import { BentoGrid, BentoGridItem } from "@/components/ui/bento-grid";
import { ContainerScroll } from "@/components/ui/container-scroll-animation";

export default function Home() {
  const { isSignedIn, isLoaded } = useUser();
  const [mounted, setMounted] = useState(false);
  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.2], [1, 0.95]);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 font-sans selection:bg-cyan-500/30 overflow-x-hidden transition-colors duration-300">
      
      {/* Background gradients */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-500/10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-emerald-500/10 blur-[120px]" />
        <div className="absolute top-[40%] left-[60%] w-[30%] h-[30%] rounded-full bg-indigo-500/10 blur-[120px]" />
      </div>

      {/* Navigation */}
      <motion.header 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="fixed top-0 w-full border-b border-zinc-200/50 dark:border-zinc-800/50 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-xl z-50 transition-colors duration-300"
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-8 w-8 rounded-xl bg-zinc-900 dark:bg-white flex items-center justify-center group-hover:scale-105 transition-transform shadow-md">
              <Sparkles className="h-4 w-4 text-white dark:text-zinc-900" />
            </div>
            <span className="font-bold text-xl tracking-tight text-zinc-900 dark:text-white">Nexus RAG</span>
          </Link>
          
          <div className="flex items-center gap-4 sm:gap-6">
            <ThemeToggle />
            
            {isLoaded && isSignedIn ? (
              <div className="flex items-center gap-4">
                <Link 
                  href="/workspace" 
                  className="hidden sm:flex items-center gap-2 px-5 py-2 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-medium text-sm hover:opacity-90 transition-opacity"
                >
                  Enter Workspace <ArrowRight className="h-4 w-4" />
                </Link>
                <UserButton afterSignOutUrl="/" appearance={{ elements: { avatarBox: "h-9 w-9 ring-2 ring-zinc-200 dark:ring-zinc-800" } }} />
              </div>
            ) : (
              <div className="flex items-center gap-4">
                <SignInButton mode="modal">
                  <button className="hidden sm:block text-zinc-600 dark:text-zinc-300 font-medium text-sm hover:text-zinc-900 dark:hover:text-white transition-colors">
                    Sign In
                  </button>
                </SignInButton>
                <Link 
                  href="/workspace" 
                  className="flex items-center gap-2 px-5 py-2 rounded-full bg-gradient-to-r from-cyan-500 to-emerald-500 text-white font-medium text-sm hover:shadow-lg hover:shadow-cyan-500/25 transition-all"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      </motion.header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 min-h-[90vh] flex flex-col justify-center z-10">
        <motion.div 
          style={{ opacity, scale }}
          className="max-w-7xl mx-auto px-6 relative text-center flex flex-col items-center"
        >
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 text-sm font-medium text-zinc-600 dark:text-zinc-300 mb-8 shadow-sm backdrop-blur-sm"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            Enterprise Engine v2.0 is live
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tighter text-zinc-900 dark:text-white mb-6 leading-[1.1]"
          >
            Unleash Your <br className="hidden sm:block"/>
            <span className="text-transparent bg-clip-text bg-gradient-to-br from-cyan-500 via-emerald-500 to-indigo-500">
              Corporate Intelligence.
            </span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="max-w-2xl mx-auto text-lg md:text-xl text-zinc-600 dark:text-zinc-400 mb-10 leading-relaxed"
          >
            Deploy a highly precise, multimodal RAG architecture. Combine Qdrant semantic search with BM25 lexical matching to extract accurate answers from PDFs, Office documents, and YouTube videos.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto"
          >
            <Link 
              href="/workspace" 
              className="flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 font-semibold hover:scale-105 transition-all shadow-xl shadow-zinc-900/20 dark:shadow-white/10 w-full sm:w-auto text-base"
            >
              Start Building <ArrowRight className="h-5 w-5" />
            </Link>
            <a 
              href="#architecture" 
              className="flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-white dark:bg-zinc-900 text-zinc-900 dark:text-white border border-zinc-200 dark:border-zinc-800 font-semibold hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors w-full sm:w-auto text-base"
            >
              View Architecture
            </a>
          </motion.div>
        </motion.div>
      </section>

      {/* Cinematic UI Reveal */}
      <section className="relative z-20 pb-32 pt-10">
        <ContainerScroll
          titleComponent={
            <div className="mb-8 text-center max-w-3xl mx-auto px-6">
              <h2 className="text-3xl md:text-5xl font-bold text-zinc-900 dark:text-white tracking-tight mb-4">
                Chat with your <span className="italic text-zinc-500">entire</span> knowledge base
              </h2>
              <p className="text-lg text-zinc-600 dark:text-zinc-400">
                Experience instant, verifiable answers backed by Gemini intelligence.
              </p>
            </div>
          }
        >
          <div className="h-full w-full bg-zinc-950 rounded-2xl border border-zinc-800 flex flex-col overflow-hidden relative shadow-2xl">
            {/* Mock Dashboard Header */}
            <div className="h-14 border-b border-zinc-800 flex items-center px-6 justify-between bg-zinc-900/50">
              <div className="flex gap-2">
                <div className="h-3 w-3 rounded-full bg-red-500/80"></div>
                <div className="h-3 w-3 rounded-full bg-yellow-500/80"></div>
                <div className="h-3 w-3 rounded-full bg-green-500/80"></div>
              </div>
              <div className="text-xs font-mono text-zinc-500 flex items-center gap-2">
                <ShieldCheck className="h-3 w-3" /> Tenant Isolated
              </div>
            </div>
            {/* Mock Dashboard Content */}
            <div className="flex-1 flex bg-zinc-950 relative overflow-hidden">
              {/* Sidebar */}
              <div className="w-64 border-r border-zinc-800 hidden md:flex flex-col p-4 gap-4">
                <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2 mt-2 px-2">Knowledge Sources</div>
                <div className="space-y-2">
                  {[
                    { icon: <Files className="h-4 w-4 text-blue-400"/>, name: "Q4_Financial_Report.pdf" },
                    { icon: <Play className="h-4 w-4 text-red-400"/>, name: "Company_All_Hands_Q3" },
                    { icon: <Files className="h-4 w-4 text-orange-400"/>, name: "Project_Phoenix.pptx" },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-3 text-sm text-zinc-300 p-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800/50 shadow-sm">
                      {item.icon} <span className="truncate">{item.name}</span>
                    </div>
                  ))}
                </div>
              </div>
              {/* Main Chat Area */}
              <div className="flex-1 p-6 flex flex-col justify-end gap-6 relative">
                {/* Background grid */}
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
                
                <div className="flex gap-4 relative z-10 w-full max-w-2xl mx-auto">
                  <div className="h-8 w-8 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0 border border-emerald-500/30">
                    <span className="text-xs font-bold text-emerald-400">ME</span>
                  </div>
                  <div className="bg-zinc-900 border border-zinc-800 p-4 rounded-2xl rounded-tl-none text-zinc-200 text-sm shadow-sm">
                    Can you summarize the main blockers mentioned in the Project Phoenix presentation and the All Hands video?
                  </div>
                </div>
                
                <div className="flex gap-4 relative z-10 w-full max-w-2xl mx-auto mb-4">
                  <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center shrink-0 shadow-md">
                    <Sparkles className="h-4 w-4 text-white" />
                  </div>
                  <div className="bg-zinc-900/90 border border-zinc-800 p-5 rounded-2xl rounded-tl-none text-zinc-300 text-sm leading-relaxed backdrop-blur-md shadow-sm">
                    <p className="mb-3">Based on the provided context, here are the main blockers:</p>
                    <ul className="list-disc pl-5 space-y-2 mb-4 text-zinc-400">
                      <li><strong className="text-zinc-200">Supply Chain Delays:</strong> The Q3 All Hands video notes a 3-week delay in component delivery (04:12).</li>
                      <li><strong className="text-zinc-200">API Integration:</strong> Project_Phoenix.pptx (Page 12) highlights pending approval from the external vendor for the v2 API endpoints.</li>
                    </ul>
                    <div className="flex items-center gap-3 mt-4 pt-4 border-t border-zinc-800/50">
                      <span className="text-xs text-zinc-500 flex items-center gap-1 font-medium"><BrainCircuit className="h-3.5 w-3.5"/> Gemini Engine</span>
                      <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20 flex items-center gap-1 tracking-wider"><Zap className="h-3 w-3"/> 124ms</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ContainerScroll>
      </section>

      {/* Feature Grid / Architecture */}
      <section id="architecture" className="py-24 px-6 relative z-20 bg-white/50 dark:bg-zinc-950/50 border-y border-zinc-200/50 dark:border-zinc-800/50">
        <div className="max-w-7xl mx-auto mb-20 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 dark:bg-cyan-500/10 border border-cyan-200 dark:border-cyan-500/20 text-cyan-600 dark:text-cyan-400 text-sm font-semibold mb-6">
            <Cpu className="h-4 w-4" /> Uncompromising Architecture
          </div>
          <h2 className="text-3xl md:text-5xl font-bold text-zinc-900 dark:text-white tracking-tight mb-6">
            Built for accuracy & scale
          </h2>
          <p className="text-lg text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            We don't just do basic vector search. Our hybrid pipeline ensures that you never miss a critical keyword while maintaining deep semantic understanding.
          </p>
        </div>

        <BentoGrid className="max-w-6xl mx-auto">
          <BentoGridItem
            title="Multimodal Ingestion Pipeline"
            description="Upload PDFs, DOCX, PPTX files, or provide YouTube URLs. Our system extracts text, isolates images, and runs Whisper transcription seamlessly."
            header={
              <div className="flex flex-1 w-full h-full min-h-[8rem] rounded-xl bg-gradient-to-br from-blue-500/10 to-indigo-500/10 border border-blue-500/20 flex items-center justify-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20 dark:opacity-40"></div>
                <Files className="w-16 h-16 text-blue-500 drop-shadow-md group-hover:scale-110 transition-transform duration-500" />
              </div>
            }
            className="md:col-span-2 shadow-sm border border-zinc-200 dark:border-zinc-800/60"
          />
          <BentoGridItem
            title="Hybrid Qdrant + BM25 Retrieval"
            description="Combines precise keyword matching (BM25) with deep semantic vector search (Qdrant) to guarantee the highest relevance."
            header={
              <div className="flex flex-1 w-full h-full min-h-[8rem] rounded-xl bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 flex items-center justify-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20 dark:opacity-40"></div>
                <Database className="w-16 h-16 text-emerald-500 drop-shadow-md group-hover:scale-110 transition-transform duration-500" />
              </div>
            }
            className="md:col-span-1 shadow-sm border border-zinc-200 dark:border-zinc-800/60"
          />
          <BentoGridItem
            title="Gemini Intelligence Synthesis"
            description="Synthesizes retrieved context using Google's Gemini models to provide accurate answers with exact verifiable citations."
            header={
              <div className="flex flex-1 w-full h-full min-h-[8rem] rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 flex items-center justify-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20 dark:opacity-40"></div>
                <BrainCircuit className="w-16 h-16 text-purple-500 drop-shadow-md group-hover:scale-110 transition-transform duration-500" />
              </div>
            }
            className="md:col-span-1 shadow-sm border border-zinc-200 dark:border-zinc-800/60"
          />
          <BentoGridItem
            title="Tenant-Isolated Workspaces"
            description="Securely partition data by user. Your documents and vector indices are strictly isolated using Supabase RLS and Qdrant collections."
            header={
              <div className="flex flex-1 w-full h-full min-h-[8rem] rounded-xl bg-gradient-to-br from-zinc-500/10 to-zinc-800/10 border border-zinc-500/20 flex items-center justify-center relative overflow-hidden group">
                <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-20 dark:opacity-40"></div>
                <ShieldCheck className="w-16 h-16 text-zinc-600 dark:text-zinc-400 drop-shadow-md group-hover:scale-110 transition-transform duration-500" />
              </div>
            }
            className="md:col-span-2 shadow-sm border border-zinc-200 dark:border-zinc-800/60"
          />
        </BentoGrid>
      </section>

      {/* Deep Dive Process / Flow */}
      <section className="py-32 px-6 relative z-20">
        <div className="max-w-4xl mx-auto text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-zinc-900 dark:text-white tracking-tight mb-6">
            From raw data to actionable intelligence
          </h2>
        </div>

        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Upload & Parse",
                description: "Drop files or URLs into your workspace. We extract text, format tables, and run Whisper on video/audio.",
                icon: <Layers className="w-6 h-6" />
              },
              {
                step: "02",
                title: "Chunk & Index",
                description: "Content is intelligently chunked and embedded. Vectors are stored in Qdrant, alongside a BM25 lexical index.",
                icon: <Database className="w-6 h-6" />
              },
              {
                step: "03",
                title: "Ask & Synthesize",
                description: "Ask natural language questions. We retrieve the most relevant chunks and synthesize answers via Gemini.",
                icon: <Sparkles className="w-6 h-6" />
              }
            ].map((feature, idx) => (
              <div key={idx} className="relative p-8 rounded-3xl bg-white dark:bg-zinc-900/50 border border-zinc-200 dark:border-zinc-800 shadow-sm hover:shadow-md transition-shadow group">
                <div className="text-zinc-100 dark:text-zinc-800/50 text-7xl font-black absolute top-4 right-6 select-none transition-colors group-hover:text-cyan-50 dark:group-hover:text-cyan-900/20">
                  {feature.step}
                </div>
                <div className="h-12 w-12 rounded-xl bg-cyan-100 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 flex items-center justify-center mb-6 relative z-10 shadow-sm">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-zinc-900 dark:text-white mb-3 relative z-10">{feature.title}</h3>
                <p className="text-zinc-600 dark:text-zinc-400 relative z-10 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6 relative z-20 overflow-hidden">
        <div className="absolute inset-0 bg-zinc-950 dark:bg-zinc-900">
          <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center opacity-15"></div>
          {/* Glowing orb */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-cyan-500/20 to-emerald-500/20 rounded-full blur-[100px] pointer-events-none"></div>
        </div>
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-4xl md:text-6xl font-bold text-white tracking-tight mb-8">
            Start talking to your data.
          </h2>
          <p className="text-xl text-zinc-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            Experience the most powerful semantic search and retrieval engine. Deploy instantly and manage your documents securely.
          </p>
          <Link 
            href="/workspace" 
            className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-white text-zinc-900 font-bold hover:scale-105 transition-all shadow-xl shadow-white/10 text-lg"
          >
            Enter Workspace <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="py-12 px-6 bg-white dark:bg-zinc-950 border-t border-zinc-200 dark:border-zinc-800 relative z-20">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-xl bg-zinc-900 dark:bg-white flex items-center justify-center shadow-sm">
              <Sparkles className="h-4 w-4 text-white dark:text-zinc-900" />
            </div>
            <span className="font-bold text-lg tracking-tight text-zinc-900 dark:text-white">Nexus RAG</span>
          </div>
          
          <div className="flex items-center gap-6 text-sm text-zinc-500 dark:text-zinc-400 font-medium">
            <Link href="/workspace" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Workspace</Link>
            <a href="#" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Documentation</a>
            <a href="https://github.com/Prakshit0902/pdf-rag" target="_blank" rel="noopener noreferrer" className="hover:text-zinc-900 dark:hover:text-white transition-colors">GitHub</a>
          </div>
          
          <div className="text-sm text-zinc-500 dark:text-zinc-500">
            © {new Date().getFullYear()} Nexus RAG. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}