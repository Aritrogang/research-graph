"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { FileText } from "lucide-react";

interface PaperNodeData {
  title: string;
  arxiv_id: string;
  year: number | string;
  authors: string[];
  isCenter: boolean;
  readingOrder?: number;
  difficulty?: string;
  reason?: string;
  [key: string]: unknown;
}

const DIFFICULTY_STYLES: Record<string, string> = {
  beginner: "bg-green-900/60 text-green-300 border-green-700",
  intermediate: "bg-amber-900/60 text-amber-300 border-amber-700",
  advanced: "bg-red-900/60 text-red-300 border-red-700",
};

export default function PaperNode({ data }: NodeProps) {
  const d = data as PaperNodeData;
  const isCenter = d.isCenter;
  const hasReadingOrder = d.readingOrder != null;

  return (
    <div
      className={`rounded-lg border px-4 py-3 shadow-lg min-w-[200px] max-w-[260px] ${
        isCenter
          ? "border-brand-500 bg-brand-900/80 ring-2 ring-brand-500/40"
          : "border-gray-700 bg-gray-800/90 hover:border-gray-500"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-brand-500" />

      {/* Reading order badge */}
      {hasReadingOrder && (
        <div className="mb-2 flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-xs font-bold text-white">
            {d.readingOrder}
          </span>
          {d.difficulty && (
            <span
              className={`rounded-full border px-2 py-0.5 text-xs font-medium ${
                DIFFICULTY_STYLES[d.difficulty] || DIFFICULTY_STYLES.intermediate
              }`}
            >
              {d.difficulty}
            </span>
          )}
        </div>
      )}

      <div className="flex items-start gap-2">
        <FileText className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" />
        <div className="min-w-0">
          <p className="text-sm font-semibold leading-tight text-gray-100 line-clamp-2">
            {d.title}
          </p>
          <p className="mt-1 text-xs text-gray-400">
            {d.year} &middot; {(d.authors ?? []).slice(0, 2).join(", ")}
            {(d.authors ?? []).length > 2 && " et al."}
          </p>
          {d.reason && (
            <p className="mt-1 text-xs text-gray-500 line-clamp-2 italic">
              {d.reason}
            </p>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-brand-500" />
    </div>
  );
}
