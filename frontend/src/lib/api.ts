const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatRequest {
  paper_id: string;
  question: string;
}

export interface ChatResponse {
  answer: string;
  source: "cache" | "llm";
  context_used: string[];
}

export interface GraphNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    title: string;
    arxiv_id: string;
    year: number | string;
    authors: string[];
    isCenter: boolean;
    readingOrder?: number;
    difficulty?: string;
    reason?: string;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  animated: boolean;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ── Discover types ──────────────────────────────────────────────────

export interface DiscoverRequest {
  topic: string;
  background: string;
  count: number;
}

export interface PaperSummary {
  id: string;
  arxiv_id: string;
  title: string;
  authors: string[];
  year: number | null;
  abstract: string;
  reading_order: number;
  difficulty: string;
  reason: string;
}

export interface DiscoverResponse {
  topic: string;
  background: string;
  papers: PaperSummary[];
}

// ── API functions ───────────────────────────────────────────────────

export async function postChat(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Chat request failed");
  }
  return res.json();
}

export async function fetchGraph(paperId: string): Promise<GraphResponse> {
  const res = await fetch(`${API_URL}/graph/${paperId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Graph fetch failed");
  }
  return res.json();
}

export async function discoverPapers(req: DiscoverRequest): Promise<DiscoverResponse> {
  const res = await fetch(`${API_URL}/discover`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Discovery failed");
  }
  return res.json();
}
