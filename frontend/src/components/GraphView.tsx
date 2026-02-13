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
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { GitFork } from "lucide-react";

import PaperNode from "@/components/PaperNode";
import { fetchGraph } from "@/lib/api";

const DEFAULT_PAPER_ID = "1706.03762"; // Attention Is All You Need

interface GraphViewProps {
  onNodeSelect: (paperId: string, title: string) => void;
}

export default function GraphView({ onNodeSelect }: GraphViewProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [graphError, setGraphError] = useState<string | null>(null);

  const nodeTypes = useMemo(() => ({ paperNode: PaperNode }), []);

  // Load initial graph on mount
  useEffect(() => {
    loadGraph(DEFAULT_PAPER_ID);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadGraph = async (paperId: string) => {
    try {
      setGraphError(null);
      const data = await fetchGraph(paperId);
      setNodes(data.nodes as Node[]);
      setEdges(data.edges as Edge[]);
    } catch (err) {
      setGraphError(err instanceof Error ? err.message : "Failed to load graph");
    }
  };

  const onNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      const data = node.data as { title?: string; arxiv_id?: string };
      onNodeSelect(node.id, data.title ?? "Unknown");

      // Expand graph: fetch citations for clicked node and merge into existing graph
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
          /* satellite paper may not be in DB yet – silently ignore */
        });
    },
    [onNodeSelect, setNodes, setEdges],
  );

  return (
    <div className="relative h-full w-full">
      <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-lg bg-gray-900/80 px-3 py-2 backdrop-blur">
        <GitFork className="h-5 w-5 text-brand-500" />
        <span className="text-sm font-semibold">ResearchGraph</span>
      </div>

      {graphError && (
        <div className="absolute left-4 top-16 z-10 rounded-lg bg-red-900/80 px-3 py-2 text-sm text-red-200">
          {graphError}
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
