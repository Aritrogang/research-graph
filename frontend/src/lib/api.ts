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
