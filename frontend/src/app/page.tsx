"use client";

import { useCallback, useState } from "react";

import TopicForm from "@/components/TopicForm";
import GraphView from "@/components/GraphView";
import ChatPanel from "@/components/ChatPanel";
import { useChat } from "@/hooks/useChat";
import { discoverPapers, type DiscoverResponse } from "@/lib/api";

export default function Dashboard() {
  // Discovery state
  const [discoverResult, setDiscoverResult] = useState<DiscoverResponse | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [discoverError, setDiscoverError] = useState<string | null>(null);

  // Graph + Chat state
  const [activePaperId, setActivePaperId] = useState<string | null>(null);
  const [activePaperTitle, setActivePaperTitle] = useState<string | null>(null);

  const { messages, loading, error, sendMessage } = useChat(activePaperId);

  const handleDiscover = useCallback(async (topic: string, background: string, count: number) => {
    setDiscovering(true);
    setDiscoverError(null);
    try {
      const result = await discoverPapers({ topic, background, count });
      setDiscoverResult(result);
      // Auto-select the first paper for chat
      if (result.papers.length > 0) {
        setActivePaperId(result.papers[0].id);
        setActivePaperTitle(result.papers[0].title);
      }
    } catch (err) {
      setDiscoverError(err instanceof Error ? err.message : "Discovery failed");
    } finally {
      setDiscovering(false);
    }
  }, []);

  const handleNodeSelect = useCallback((paperId: string, title: string) => {
    setActivePaperId(paperId);
    setActivePaperTitle(title);
  }, []);

  const handleReset = useCallback(() => {
    setDiscoverResult(null);
    setActivePaperId(null);
    setActivePaperTitle(null);
    setDiscoverError(null);
  }, []);

  // Show topic form if no discovery yet
  if (!discoverResult) {
    return (
      <div>
        <TopicForm onSubmit={handleDiscover} loading={discovering} />
        {discoverError && (
          <div className="fixed bottom-6 left-1/2 -translate-x-1/2 rounded-lg bg-red-900/90 px-4 py-2 text-sm text-red-200 shadow-lg">
            {discoverError}
          </div>
        )}
      </div>
    );
  }

  // Show graph + chat after discovery
  return (
    <div className="flex h-screen">
      {/* Left panel – Graph (65%) */}
      <div className="w-[65%]">
        <GraphView
          onNodeSelect={handleNodeSelect}
          discoveredPapers={discoverResult.papers}
          topic={discoverResult.topic}
          onReset={handleReset}
        />
      </div>

      {/* Right panel – Chat (35%) */}
      <div className="w-[35%]">
        <ChatPanel
          messages={messages}
          loading={loading}
          error={error}
          activePaperTitle={activePaperTitle}
          onSend={sendMessage}
        />
      </div>
    </div>
  );
}
