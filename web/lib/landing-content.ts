import type { LucideIcon } from "lucide-react";
import {
  FileText,
  Presentation,
  FileType2,
  Video,
  Upload,
  MessageSquareText,
  Quote,
  Search,
  Layers,
  ShieldCheck,
  Sparkles,
  Clock,
} from "lucide-react";

export const brand = {
  name: "Omni RAG",
  tagline: "Ask your documents anything.",
  repoUrl: "https://github.com/Prakshit0902/pdf-rag",
};

export const nav = {
  links: [
    { label: "How it works", href: "#how-it-works" },
    { label: "Features", href: "#features" },
    { label: "Live demo", href: "#demo" },
    { label: "FAQ", href: "#faq" },
  ],
};

export const hero = {
  eyebrow: "Reading, so you don't have to",
  titleLead: "Stop scrolling through",
  titleRotators: ["100-page PDFs.", "dense slide decks.", "hour-long videos.", "messy reports."],
  titleTail: "Just ask.",
  subtitle:
    "Drop in your PDFs, Word docs, slide decks, or a YouTube link. Ask a question in plain English and get a clear answer back, with the exact page or timestamp it came from.",
  primaryCta: "Open the workspace",
  secondaryCta: "See it in action",
  footnote: "Free to try. Your files stay private to your account.",
};

export type FileFormat = {
  label: string;
  ext: string;
  icon: LucideIcon;
};

export const formats: FileFormat[] = [
  { label: "PDF documents", ext: "PDF", icon: FileText },
  { label: "Word documents", ext: "DOCX", icon: FileType2 },
  { label: "PowerPoint decks", ext: "PPTX", icon: Presentation },
  { label: "YouTube videos", ext: "YOUTUBE", icon: Video },
];

export type Step = {
  index: string;
  title: string;
  description: string;
  icon: LucideIcon;
};

export const steps: Step[] = [
  {
    index: "01",
    title: "Add your sources",
    description:
      "Upload a file or paste a YouTube link. We read the text, pull out the images, and transcribe any audio automatically.",
    icon: Upload,
  },
  {
    index: "02",
    title: "Ask in plain English",
    description:
      "Type a question the way you'd ask a colleague. No keywords, no special syntax, no prompt tricks required.",
    icon: MessageSquareText,
  },
  {
    index: "03",
    title: "Get a cited answer",
    description:
      "Read a clear answer that streams in as it's written, with the exact page numbers and timestamps it came from.",
    icon: Quote,
  },
];

export type Feature = {
  id: string;
  eyebrow: string;
  title: string;
  description: string;
  bullets: string[];
  icon: LucideIcon;
  visual: "answer" | "search" | "formats" | "privacy";
};

export const features: Feature[] = [
  {
    id: "cited-answers",
    eyebrow: "Trust the answer",
    title: "Every answer shows its work",
    description:
      "No more guessing whether a chatbot made something up. Each response points straight back to the page, slide, or moment in the video it was drawn from, so you can verify it in a click.",
    bullets: [
      "Exact page numbers for documents",
      "Timestamps for video and audio",
      "Open the source without leaving the chat",
    ],
    icon: Quote,
    visual: "answer",
  },
  {
    id: "hybrid-search",
    eyebrow: "Find what matters",
    title: "Search by meaning and by exact words",
    description:
      "Most tools only match meaning, so they miss precise terms like part numbers, names, or clause references. We search both ways at once and rank what's most relevant, so nothing important slips through.",
    bullets: [
      "Understands what you mean, not just what you typed",
      "Still catches exact terms and figures",
      "Pulls the most relevant passages to the top",
    ],
    icon: Search,
    visual: "search",
  },
  {
    id: "multimodal",
    eyebrow: "Everything in one place",
    title: "Mix documents, decks, and videos",
    description:
      "Your knowledge isn't all in one format, and it shouldn't have to be. Bring reports, presentations, and recorded talks into a single workspace and ask questions across all of them together.",
    bullets: [
      "PDFs, Word docs, and PowerPoint",
      "YouTube videos, transcribed for you",
      "Ask one question across every source",
    ],
    icon: Layers,
    visual: "formats",
  },
  {
    id: "private",
    eyebrow: "Yours alone",
    title: "Your documents stay your documents",
    description:
      "Sign in and your files, conversations, and history are tied to your account and no one else's. Come back later and pick up exactly where you left off.",
    bullets: [
      "Secure sign-in on every session",
      "Files scoped to your account only",
      "Conversation history saved for next time",
    ],
    icon: ShieldCheck,
    visual: "privacy",
  },
];

export type DemoSource = {
  tag: string;
  text: string;
};

export const demo = {
  question: "What was our revenue growth in Q4, and what drove it?",
  sources: [
    { tag: "Q4_Report.pdf · p.12", text: "Total revenue reached $48.2M, up 31% year over year." },
    { tag: "Q4_Report.pdf · p.14", text: "Growth was led by enterprise renewals and the new EU region." },
    { tag: "Earnings_Call.mp4 · 12:04", text: "\u201cMost of the lift came from expansion in existing accounts.\u201d" },
  ] as DemoSource[],
  answer:
    "Q4 revenue grew **31% year over year** to **$48.2M**. The increase was driven mainly by **enterprise renewals** and **expansion within existing accounts**, with additional momentum from the newly launched **EU region**.",
  citations: ["p.12", "p.14", "12:04"],
};

export type Capability = {
  value: string;
  label: string;
  icon: LucideIcon;
};

export const capabilities: Capability[] = [
  { value: "4", label: "Source types in one place", icon: Layers },
  { value: "Real-time", label: "Answers stream as they're written", icon: Clock },
  { value: "Page-exact", label: "Citations you can verify", icon: Quote },
  { value: "Private", label: "Scoped to your account", icon: ShieldCheck },
];

export type FaqItem = {
  question: string;
  answer: string;
};

export const faqs: FaqItem[] = [
  {
    question: "What kinds of files can I use?",
    answer:
      "PDFs, Word documents (DOCX), and PowerPoint decks (PPTX), plus YouTube links. For videos, the audio is transcribed automatically so you can ask about what was said.",
  },
  {
    question: "How do I know the answers are accurate?",
    answer:
      "Every answer is built from your sources and shows exactly where it came from, down to the page number or video timestamp. You can open the original passage in a click to confirm it yourself.",
  },
  {
    question: "Do I need to learn any special commands?",
    answer:
      "No. Ask questions the same way you'd ask a colleague. There's no syntax to memorize and no prompt engineering required.",
  },
  {
    question: "What happens to my documents?",
    answer:
      "You sign in before using the workspace, and your files and conversations are tied to your account. They aren't shared with other users, and your history is saved so you can return to it later.",
  },
  {
    question: "Can it handle long documents and big videos?",
    answer:
      "Yes. Whether it's a hundred-page report or an hour-long talk, you can ask targeted questions and get back just the part you need instead of reading the whole thing.",
  },
];

export const finalCta = {
  title: "Your next answer is one question away.",
  subtitle:
    "Bring in a document or a video and start asking. It takes less than a minute to get your first cited answer.",
  primary: "Open the workspace",
  badge: "No setup. No reading the manual.",
};

export const footer = {
  tagline: "Ask your documents anything, and get answers you can trust.",
  columns: [
    {
      title: "Product",
      links: [
        { label: "How it works", href: "#how-it-works" },
        { label: "Features", href: "#features" },
        { label: "Live demo", href: "#demo" },
        { label: "FAQ", href: "#faq" },
      ],
    },
    {
      title: "Get started",
      links: [
        { label: "Open workspace", href: "/workspace" },
        { label: "GitHub", href: brand.repoUrl },
      ],
    },
  ],
};

export const accentIcon = Sparkles;
