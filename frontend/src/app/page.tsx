"use client";

import { useCallback, useState } from "react";

import GraphView from "@/components/GraphView";
import ChatPanel from "@/components/ChatPanel";
import { useChat } from "@/hooks/useChat";

export default function Dashboard() {
  const [activePaperId, setActivePaperId] = useState<string | null>(null);
  const [activePaperTitle, setActivePaperTitle] = useState<string | null>(null);

  const { messages, loading, error, sendMessage } = useChat(activePaperId);

  const handleNodeSelect = useCallback((paperId: string, title: string) => {
    setActivePaperId(paperId);
    setActivePaperTitle(title);
  }, []);

  return (
    <div className="flex h-screen">
      {/* Left panel – Graph (65%) */}
      <div className="w-[65%]">
        <GraphView onNodeSelect={handleNodeSelect} />
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
