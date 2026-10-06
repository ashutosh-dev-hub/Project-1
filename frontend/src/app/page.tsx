"use client";

import { useState } from "react";

interface Message {
  role: "user" | "agent" | "error";
  content: string;
  logs?: string[];
  pending_action?: any;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (textToSend?: string) => {
    const userMessage = (textToSend || input).trim();
    if (!userMessage) return;

    const newHistory = [...messages, { role: "user" as const, content: userMessage }];
    setMessages(newHistory);
    setInput("");
    setLoading(true);

    try {
      // Send recent message history so Planner maintains context across turns
      const historyPayload = newHistory.slice(-8).map((m) => ({
        role: m.role,
        content: m.content,
      }));

      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message: userMessage, 
          history: historyPayload 
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            role: "agent",
            content: data.reply,
            logs: data.agent_logs,
            pending_action: data.pending_action,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "error", content: data.detail?.error || "Error occurred during execution" },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", content: String(err) }]);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (action: any, index: number) => {
    // Clear pending_action from the previous message to prevent duplicate clicks
    setMessages((prev) =>
      prev.map((msg, i) => (i === index ? { ...msg, pending_action: null } : msg))
    );

    setMessages((prev) => [
      ...prev,
      { role: "user", content: `Approved Action: ${action.tool_name}` },
    ]);
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "",
          pending_action_approved: action,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            role: "agent",
            content: data.reply,
            logs: data.agent_logs,
            pending_action: data.pending_action,
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "error", content: data.detail?.error || "Error occurred during resumption" },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { role: "error", content: String(err) }]);
    } finally {
      setLoading(false);
    }
  };

  const quickPrompts = [
    "Search web for latest AI news",
    "Check system info and CPU usage",
    "List top running processes",
    "Find files named resume",
    "Remember that my favorite browser is Brave",
    "Open https://github.com",
  ];

  return (
    <div className="min-h-screen bg-neutral-950 text-white flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-3xl bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[85vh]">
        
        {/* Header */}
        <div className="bg-neutral-800/80 backdrop-blur px-6 py-4 border-b border-neutral-700/60 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-3.5 h-3.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">AI OS — Intelligent System Layer</h1>
              <p className="text-xs text-neutral-400">Windows Multi-Agent Automation</p>
            </div>
          </div>
          <div className="flex gap-2 text-xs">
            <span className="px-2.5 py-1 rounded-full bg-neutral-800 text-neutral-300 border border-neutral-700 font-mono">
              FileAgent
            </span>
            <span className="px-2.5 py-1 rounded-full bg-neutral-800 text-neutral-300 border border-neutral-700 font-mono">
              SystemAgent
            </span>
            <span className="px-2.5 py-1 rounded-full bg-neutral-800 text-neutral-300 border border-neutral-700 font-mono">
              MemoryAgent
            </span>
            <span className="px-2.5 py-1 rounded-full bg-neutral-800 text-neutral-300 border border-neutral-700 font-mono">
              BrowserAgent
            </span>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center text-neutral-400 py-12">
              <div className="text-4xl mb-3">💻</div>
              <h2 className="text-lg font-semibold text-neutral-200">Welcome to AI OS</h2>
              <p className="text-sm text-neutral-400 max-w-md mt-1 mb-6">
                Interact with your operating system using plain English. Inspect files, launch applications, check diagnostics, or execute multi-step workflows.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {quickPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(prompt)}
                    className="text-xs bg-neutral-800 hover:bg-neutral-700 text-neutral-300 px-3 py-1.5 rounded-lg border border-neutral-700 transition"
                  >
                    ⚡ {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-4 py-3 rounded-xl max-w-[85%] ${
                msg.role === 'user' 
                  ? 'bg-blue-600 text-white rounded-br-xs' 
                  : msg.role === 'error' 
                  ? 'bg-rose-950/80 border border-rose-800 text-rose-200' 
                  : 'bg-neutral-800 border border-neutral-700/60 rounded-bl-xs'
              }`}>
                <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>

                {/* Execution Logs */}
                {msg.logs && msg.logs.length > 0 && (
                  <details className="mt-3 group">
                    <summary className="cursor-pointer text-xs font-semibold text-neutral-400 hover:text-neutral-300 mb-1 list-none flex items-center select-none">
                      <span className="mr-1.5 inline-block transition-transform group-open:rotate-90 text-[10px]">▶</span>
                      Execution Logs ({msg.logs.length} steps)
                    </summary>
                    <div className="p-3 bg-black/40 border border-neutral-800 rounded-lg text-xs text-neutral-300 font-mono overflow-x-auto mt-2 space-y-1">
                      {msg.logs.map((log, i) => (
                        <div key={i} className={log.includes("SECURITY ALERT") ? "text-amber-400 font-semibold" : log.includes("Error") ? "text-rose-400" : log.includes("Success") ? "text-emerald-400" : ""}>
                          {log}
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                {/* Safety Confirmation Alert */}
                {msg.pending_action && (
                  <div className="mt-4 p-3.5 bg-amber-950/40 border border-amber-600/50 rounded-xl">
                    <div className="flex items-center gap-2 text-sm font-semibold text-amber-400 mb-1.5">
                      <span>⚠️</span> Human Verification Required
                    </div>
                    <div className="text-xs text-neutral-300 mb-3">
                      The AI OS is requesting permission to execute high-risk action:{" "}
                      <span className="font-mono text-amber-300 font-semibold">{msg.pending_action.tool_name}</span>
                      {msg.pending_action.arguments && (
                        <div className="mt-1 font-mono text-[11px] text-neutral-400 bg-black/30 p-1.5 rounded">
                          {JSON.stringify(msg.pending_action.arguments)}
                        </div>
                      )}
                    </div>
                    <button 
                      onClick={() => handleApprove(msg.pending_action, idx)}
                      className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-neutral-950 font-semibold rounded-lg transition-colors text-sm shadow-md"
                    >
                      Approve & Resume Execution
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="px-4 py-2.5 rounded-xl bg-neutral-800 border border-neutral-700/60 text-sm text-neutral-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500 animate-ping"></span>
                AI OS Reasoning & Executing...
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 bg-neutral-800/80 border-t border-neutral-700/60 flex flex-col gap-2">
          <div className="flex gap-2">
            <input 
              type="text"
              className="flex-1 bg-neutral-900 border border-neutral-700 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition text-white placeholder-neutral-500"
              placeholder="Give a command (e.g. Find resume, check CPU usage, open Chrome)..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button 
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-6 py-2.5 rounded-xl font-medium text-sm transition-colors shadow-md"
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
