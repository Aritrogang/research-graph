"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeMouseHandler,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { GitFork, RotateCcw } from "lucide-react";

import PaperNode from "@/components/PaperNode";
import { fetchGraph, type PaperSummary } from "@/lib/api";

interface GraphViewProps {
  onNodeSelect: (paperId: string, title: string) => void;
  discoveredPapers?: PaperSummary[];
  topic?: string;
  onReset?: () => void;
}

/** Build a zigzag reading-path layout from discovered papers. */
function buildReadingPath(papers: PaperSummary[]): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = papers.map((p, i) => ({
    id: p.id,
    type: "paperNode",
    position: {
      x: i % 2 === 0 ? 80 : 450,
      y: i * 220,
    },
    data: {
      title: p.title,
      arxiv_id: p.arxiv_id,
      year: p.year ?? "N/A",
      authors: p.authors,
      isCenter: i === 0,
      readingOrder: p.reading_order,
      difficulty: p.difficulty,
      reason: p.reason,
    },
  }));

  const edges: Edge[] = [];
  for (let i = 0; i < papers.length - 1; i++) {
    edges.push({
      id: `path-${papers[i].id}-${papers[i + 1].id}`,
      source: papers[i].id,
      target: papers[i + 1].id,
      type: "smoothstep",
      animated: true,
      markerEnd: { type: MarkerType.ArrowClosed, color: "#8b5cf6" },
      style: { stroke: "#8b5cf6", strokeWidth: 2 },
    });
  }

  return { nodes, edges };
}

export default function GraphView({
  onNodeSelect,
  discoveredPapers,
  topic,
  onReset,
}: GraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [graphError, setGraphError] = useState<string | null>(null);

  const nodeTypes = useMemo(() => ({ paperNode: PaperNode }), []);

  // When discovered papers change, build the reading path
  useEffect(() => {
    if (discoveredPapers && discoveredPapers.length > 0) {
      const { nodes: pathNodes, edges: pathEdges } = buildReadingPath(discoveredPapers);
      setNodes(pathNodes);
      setEdges(pathEdges);
      setGraphError(null);
    }
  }, [discoveredPapers, setNodes, setEdges]);

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      const data = node.data as { title?: string; arxiv_id?: string };
      onNodeSelect(node.id, data.title ?? "Unknown");

      // Expand graph: fetch citations for clicked node and merge
      const arxivId = data.arxiv_id;
      if (!arxivId) return;

      fetchGraph(arxivId)
        .then((newData) => {
          setNodes((prev) => {
            const existingIds = new Set(prev.map((n) => n.id));
            const fresh = (newData.nodes as Node[]).filter((n) => !existingIds.has(n.id));
            return [...prev, ...fresh];
          });
          setEdges((prev) => {
            const existingIds = new Set(prev.map((e) => e.id));
            const fresh = (newData.edges as Edge[]).filter((e) => !existingIds.has(e.id));
            return [...prev, ...fresh];
          });
        })
        .catch(() => {
          /* satellite paper may not be in DB yet */
        });
    },
    [onNodeSelect, setNodes, setEdges],
  );

  return (
    <div className="relative h-full w-full">
      {/* Header */}
      <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-lg bg-gray-900/80 px-3 py-2 backdrop-blur">
        <GitFork className="h-5 w-5 text-brand-500" />
        <span className="text-sm font-semibold">
          {topic ? `Reading Path: ${topic}` : "ResearchGraph"}
        </span>
        {onReset && (
          <button
            onClick={onReset}
            className="ml-2 rounded p-1 text-gray-400 hover:bg-gray-700 hover:text-gray-200"
            title="New search"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        )}
      </div>

      {graphError && (
        <div className="absolute left-4 top-16 z-10 rounded-lg bg-red-900/80 px-3 py-2 text-sm text-red-200">
          {graphError}
        </div>
      )}

      {/* Legend */}
      {discoveredPapers && discoveredPapers.length > 0 && (
        <div className="absolute right-4 top-4 z-10 rounded-lg bg-gray-900/80 px-3 py-2 text-xs backdrop-blur">
          <p className="mb-1.5 font-semibold text-gray-300">Difficulty</p>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
              <span className="text-gray-400">Beginner</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
              <span className="text-gray-400">Intermediate</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
              <span className="text-gray-400">Advanced</span>
            </div>
          </div>
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        className="bg-gray-950"
      >
        <Background color="#374151" gap={20} />
        <Controls className="!bg-gray-800 !border-gray-700 !text-gray-300 [&>button]:!bg-gray-800 [&>button]:!border-gray-700 [&>button]:!text-gray-300 [&>button:hover]:!bg-gray-700" />
      </ReactFlow>
    </div>
  );
}
