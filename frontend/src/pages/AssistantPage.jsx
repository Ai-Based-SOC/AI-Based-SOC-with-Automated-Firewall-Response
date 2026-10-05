import { useState } from "react";
import PageShell from "../components/PageShell";
import Panel from "../components/Panel";
import { askAssistantApi } from "../services/api";

const quickQuestions = [
  "Show recent critical incidents",
  "Why are active threats increasing?",
  "Show firewall status",
  "Summarize system health",
];

export default function AssistantPage({ profile, onLogout }) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState([]);

  async function ask(value = message) {
    const text = value.trim();
    if (!text || busy) return;

    setBusy(true);
    setMessages((current) => [
      ...current,
      { role: "user", content: text },
    ]);
    setMessage("");

    try {
      const response = await askAssistantApi(text, messages);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            response.data?.answer ||
            response.data?.message ||
            "No answer was returned.",
        },
      ]);
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            "The assistant backend is unavailable. Check system health and try again.",
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <PageShell
      title="AI Security Assistant"
      profile={profile}
      onLogout={onLogout}
    >
      <div className="mx-auto grid max-w-[1400px] grid-cols-1 gap-4 xl:grid-cols-[1fr_280px]">
        <Panel title="AI Security Assistant">
          <div className="flex min-h-[600px] flex-col">
            <div className="flex-1 space-y-3 overflow-y-auto">
              {messages.length === 0 && (
                <div className="rounded-lg border border-cyan-900 bg-[#041326] p-4 text-sm text-slate-400">
                  Ask about incidents, threats, firewall actions, or system
                  health.
                </div>
              )}

              {messages.map((item, index) => (
                <div
                  key={index}
                  className={`max-w-[85%] rounded-lg p-3 text-sm ${
                    item.role === "user"
                      ? "ml-auto bg-blue-600 text-white"
                      : "bg-[#102847] text-slate-200"
                  }`}
                >
                  {item.content}
                </div>
              ))}
            </div>

            <div className="mt-4 flex gap-2">
              <input
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") ask();
                }}
                placeholder="Type your question..."
                className="flex-1 rounded-lg border border-cyan-900 bg-[#041326] px-3 py-2 text-sm outline-none focus:border-cyan-400"
              />

              <button
                type="button"
                onClick={() => ask()}
                disabled={busy}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm hover:bg-blue-500 disabled:opacity-50"
              >
                {busy ? "..." : "Ask"}
              </button>
            </div>
          </div>
        </Panel>

        <Panel title="Quick Questions">
          <div className="space-y-2">
            {quickQuestions.map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => ask(question)}
                className="w-full rounded-lg border border-cyan-900 px-3 py-2 text-left text-xs text-slate-300 hover:bg-cyan-950"
              >
                {question}
              </button>
            ))}
          </div>
        </Panel>
      </div>
    </PageShell>
  );
}