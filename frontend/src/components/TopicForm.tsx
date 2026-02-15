"use client";

import { useState } from "react";
import { Search, GraduationCap, BookOpen, Loader2 } from "lucide-react";

const BACKGROUND_OPTIONS = [
  "High school student",
  "Freshman in college",
  "Undergraduate (junior/senior)",
  "Graduate student (MS)",
  "PhD student / Researcher",
  "Industry professional",
];

interface TopicFormProps {
  onSubmit: (topic: string, background: string, count: number) => void;
  loading: boolean;
}

export default function TopicForm({ onSubmit, loading }: TopicFormProps) {
  const [topic, setTopic] = useState("");
  const [background, setBackground] = useState(BACKGROUND_OPTIONS[1]);
  const [count, setCount] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || loading) return;
    onSubmit(topic.trim(), background, count);
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gray-950 px-4">
      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mb-3 flex items-center justify-center gap-3">
            <BookOpen className="h-10 w-10 text-brand-500" />
            <h1 className="text-4xl font-bold text-gray-100">ResearchGraph</h1>
          </div>
          <p className="text-gray-400">
            Enter a scientific topic to discover a personalized reading path
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Topic */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">
              <Search className="mr-1.5 inline h-4 w-4" />
              Scientific Topic
            </label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. quantum computing, CRISPR gene editing, transformer models..."
              disabled={loading}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
            />
          </div>

          {/* Background */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">
              <GraduationCap className="mr-1.5 inline h-4 w-4" />
              Your Background
            </label>
            <select
              value={background}
              onChange={(e) => setBackground(e.target.value)}
              disabled={loading}
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-gray-100 focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-50"
            >
              {BACKGROUND_OPTIONS.map((opt) => (
                <option key={opt} value={opt}>
                  {opt}
                </option>
              ))}
            </select>
          </div>

          {/* Paper count */}
          <div>
            <label className="mb-1.5 block text-sm font-medium text-gray-300">
              Number of Papers: {count}
            </label>
            <input
              type="range"
              min={3}
              max={10}
              value={count}
              onChange={(e) => setCount(Number(e.target.value))}
              disabled={loading}
              className="w-full accent-brand-500 disabled:opacity-50"
            />
            <div className="mt-1 flex justify-between text-xs text-gray-500">
              <span>3</span>
              <span>10</span>
            </div>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={!topic.trim() || loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 py-3 font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Searching arXiv &amp; building reading path...
              </>
            ) : (
              <>
                <Search className="h-5 w-5" />
                Discover Papers
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
