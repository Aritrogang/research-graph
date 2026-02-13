"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import { FileText } from "lucide-react";

interface PaperNodeData {
  title: string;
  arxiv_id: string;
  year: number | string;
  authors: string[];
  isCenter: boolean;
  [key: string]: unknown;
}

export default function PaperNode({ data }: NodeProps) {
  const d = data as PaperNodeData;
  const isCenter = d.isCenter;

  return (
    <div
      className={`rounded-lg border px-4 py-3 shadow-lg min-w-[180px] max-w-[240px] ${
        isCenter
          ? "border-brand-500 bg-brand-900/80 ring-2 ring-brand-500/40"
          : "border-gray-700 bg-gray-800/90 hover:border-gray-500"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-brand-500" />
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
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-brand-500" />
    </div>
  );
}
