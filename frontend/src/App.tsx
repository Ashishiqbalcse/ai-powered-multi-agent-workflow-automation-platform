import {
  Activity,
  Check,
  Clock3,
  DollarSign,
  FileText,
  Play,
  RefreshCw,
  ShieldCheck,
  SquareCode,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

import {
  AgentEvent,
  TaskRun,
  createRun,
  decideApproval,
  getRun,
  listRuns,
  wsRunUrl,
} from "./lib/api";

const statusStyles: Record<string, string> = {
  queued: "border-stone-300 bg-stone-100 text-stone-700",
  running: "border-blue-200 bg-blue-50 text-blue-700",
  waiting_approval: "border-amber-200 bg-amber-50 text-amber-800",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  failed: "border-red-200 bg-red-50 text-red-700",
  stopped: "border-zinc-300 bg-zinc-100 text-zinc-700",
};

function App() {
  const [goal, setGoal] = useState(
    "Research top 5 AI startups, write a comparison table, and recommend chart ideas",
  );
  const [budgetUsd, setBudgetUsd] = useState(2);
  const [runs, setRuns] = useState<TaskRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<TaskRun | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedRunId = selectedRun?.id;

  useEffect(() => {
    void refreshRuns();
  }, []);

  useEffect(() => {
    if (!selectedRunId) return;

    const socket = new WebSocket(wsRunUrl(selectedRunId));
    socket.onmessage = (message) => {
      const payload = JSON.parse(message.data);
      if (payload.type === "event_history") {
        setEvents(payload.events ?? []);
      }
      if (payload.type === "agent_event") {
        setEvents((current) => [...current, payload.event]);
        void refreshSelectedRun(selectedRunId);
      }
    };
    socket.onerror = () => setError("Live trace connection failed.");
    return () => socket.close();
  }, [selectedRunId]);

  const costPercent = useMemo(() => {
    if (!selectedRun || selectedRun.budget_usd <= 0) return 0;
    return Math.min(100, Math.round((selectedRun.cost_usd / selectedRun.budget_usd) * 100));
  }, [selectedRun]);

  async function refreshRuns() {
    const data = await listRuns();
    setRuns(data);
    if (!selectedRun && data.length > 0) {
      setSelectedRun(data[0]);
      void refreshSelectedRun(data[0].id);
    }
  }

  async function refreshSelectedRun(runId: string) {
    const data = await getRun(runId);
    setSelectedRun(data);
    setRuns((current) => current.map((run) => (run.id === data.id ? data : run)));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const run = await createRun(goal, budgetUsd);
      setSelectedRun(run);
      setEvents([]);
      await refreshRuns();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Unable to create run.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleApproval(approved: boolean) {
    if (!selectedRun) return;
    setError(null);
    try {
      const run = await decideApproval(selectedRun.id, approved);
      setSelectedRun(run);
      await refreshRuns();
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Unable to submit approval.");
    }
  }

  return (
    <main className="min-h-screen text-zinc-950">
      <div className="mx-auto grid min-h-screen w-full max-w-[1440px] grid-cols-1 gap-0 lg:grid-cols-[340px_1fr]">
        <aside className="border-r border-zinc-200 bg-white px-5 py-5">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold tracking-normal">Agent Runs</h1>
              <p className="text-sm text-zinc-500">{runs.length} tracked</p>
            </div>
            <button
              className="grid h-9 w-9 place-items-center rounded-md border border-zinc-200 text-zinc-700 hover:bg-zinc-50"
              onClick={() => void refreshRuns()}
              title="Refresh runs"
              type="button"
            >
              <RefreshCw size={17} />
            </button>
          </div>

          <form className="space-y-3" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-zinc-700">Goal</span>
              <textarea
                className="min-h-32 w-full resize-y rounded-md border border-zinc-300 bg-white px-3 py-2 text-sm leading-6 outline-none ring-blue-500/20 focus:border-blue-500 focus:ring-4"
                value={goal}
                onChange={(event) => setGoal(event.target.value)}
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-sm font-medium text-zinc-700">Budget USD</span>
              <input
                className="h-10 w-full rounded-md border border-zinc-300 px-3 text-sm outline-none ring-blue-500/20 focus:border-blue-500 focus:ring-4"
                min="0.25"
                step="0.25"
                type="number"
                value={budgetUsd}
                onChange={(event) => setBudgetUsd(Number(event.target.value))}
              />
            </label>

            <button
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-zinc-950 px-3 text-sm font-medium text-white hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
              disabled={isSubmitting || goal.trim().length < 5}
              type="submit"
            >
              <Play size={16} />
              Start run
            </button>
          </form>

          {error && (
            <div className="mt-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mt-6 space-y-2">
            {runs.map((run) => (
              <button
                className={`w-full rounded-md border px-3 py-3 text-left transition hover:border-zinc-400 ${
                  selectedRun?.id === run.id ? "border-zinc-900 bg-zinc-50" : "border-zinc-200 bg-white"
                }`}
                key={run.id}
                onClick={() => {
                  setSelectedRun(run);
                  void refreshSelectedRun(run.id);
                }}
                type="button"
              >
                <div className="mb-2 flex items-center justify-between gap-2">
                  <StatusBadge status={run.status} />
                  <span className="text-xs text-zinc-500">{formatTime(run.created_at)}</span>
                </div>
                <p className="line-clamp-2 text-sm font-medium leading-5 text-zinc-800">{run.goal}</p>
              </button>
            ))}
          </div>
        </aside>

        <section className="min-w-0 px-5 py-5 md:px-7">
          <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0">
              <div className="mb-2 flex items-center gap-2">
                <Activity size={20} className="text-blue-700" />
                <h2 className="truncate text-xl font-semibold tracking-normal">
                  {selectedRun ? selectedRun.goal : "No run selected"}
                </h2>
              </div>
              {selectedRun && (
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={selectedRun.status} />
                  <span className="text-sm text-zinc-500">Run {shortId(selectedRun.id)}</span>
                </div>
              )}
            </div>
            {selectedRun && (
              <button
                className="flex h-9 items-center justify-center gap-2 rounded-md border border-zinc-200 bg-white px-3 text-sm text-zinc-700 hover:bg-zinc-50"
                onClick={() => void refreshSelectedRun(selectedRun.id)}
                title="Refresh selected run"
                type="button"
              >
                <RefreshCw size={16} />
                Refresh
              </button>
            )}
          </div>

          {selectedRun ? (
            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
              <div className="space-y-4">
                <ApprovalPanel run={selectedRun} onDecision={handleApproval} />
                <TracePanel events={events} />
                <AuditTable run={selectedRun} />
              </div>
              <div className="space-y-4">
                <CostPanel run={selectedRun} costPercent={costPercent} />
                <ResultPanel run={selectedRun} />
              </div>
            </div>
          ) : (
            <div className="rounded-md border border-zinc-200 bg-white p-6 text-sm text-zinc-500">
              Start a run to see the live trace.
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={`inline-flex h-6 items-center rounded-md border px-2 text-xs font-medium ${
        statusStyles[status] ?? statusStyles.queued
      }`}
    >
      {status.replace("_", " ")}
    </span>
  );
}

function ApprovalPanel({
  run,
  onDecision,
}: {
  run: TaskRun;
  onDecision: (approved: boolean) => Promise<void>;
}) {
  if (run.status !== "waiting_approval" || !run.approval_payload) return null;

  const subtasks = Array.isArray(run.approval_payload.subtasks)
    ? (run.approval_payload.subtasks as Array<Record<string, unknown>>)
    : [];

  return (
    <section className="rounded-md border border-amber-200 bg-amber-50 p-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <ShieldCheck size={18} className="text-amber-700" />
          <h3 className="text-sm font-semibold text-amber-950">Approval Gate</h3>
        </div>
        <div className="flex gap-2">
          <button
            className="grid h-9 w-9 place-items-center rounded-md border border-emerald-300 bg-white text-emerald-700 hover:bg-emerald-50"
            onClick={() => void onDecision(true)}
            title="Approve run"
            type="button"
          >
            <Check size={17} />
          </button>
          <button
            className="grid h-9 w-9 place-items-center rounded-md border border-red-300 bg-white text-red-700 hover:bg-red-50"
            onClick={() => void onDecision(false)}
            title="Stop run"
            type="button"
          >
            <X size={17} />
          </button>
        </div>
      </div>
      <div className="space-y-2">
        {subtasks.map((task, index) => (
          <div className="rounded-md border border-amber-200 bg-white px-3 py-2" key={index}>
            <div className="text-sm font-medium text-zinc-900">{String(task.title ?? "Untitled")}</div>
            <div className="mt-1 text-xs text-zinc-500">
              {String(task.agent_name ?? "agent")} · {String(task.risk_level ?? "risk")}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function TracePanel({ events }: { events: AgentEvent[] }) {
  return (
    <section className="rounded-md border border-zinc-200 bg-white">
      <div className="flex h-12 items-center justify-between border-b border-zinc-200 px-4">
        <div className="flex items-center gap-2">
          <Clock3 size={17} className="text-teal-700" />
          <h3 className="text-sm font-semibold">Live Trace</h3>
        </div>
        <span className="text-xs text-zinc-500">{events.length} events</span>
      </div>
      <div className="max-h-[430px] overflow-auto">
        {events.length === 0 ? (
          <div className="p-4 text-sm text-zinc-500">Waiting for events.</div>
        ) : (
          events.map((event) => (
            <div className="border-b border-zinc-100 px-4 py-3 last:border-b-0" key={event.id}>
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                  {event.agent_name}
                </span>
                <span className="text-xs text-zinc-500">{event.event_type}</span>
                <span className="ml-auto text-xs text-zinc-400">{formatTime(event.created_at)}</span>
              </div>
              <p className="text-sm leading-5 text-zinc-800">{event.message}</p>
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function CostPanel({ run, costPercent }: { run: TaskRun; costPercent: number }) {
  return (
    <section className="rounded-md border border-zinc-200 bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <DollarSign size={17} className="text-emerald-700" />
        <h3 className="text-sm font-semibold">Cost</h3>
      </div>
      <div className="mb-2 flex items-end justify-between">
        <span className="text-2xl font-semibold">${run.cost_usd.toFixed(4)}</span>
        <span className="text-sm text-zinc-500">of ${run.budget_usd.toFixed(2)}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-zinc-100">
        <div
          className={`h-full ${costPercent >= 80 ? "bg-amber-500" : "bg-emerald-600"}`}
          style={{ width: `${costPercent}%` }}
        />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
        <Metric label="Iterations" value={`${run.iterations}/${run.max_iterations}`} />
        <Metric label="API calls" value={String(run.api_calls?.length ?? 0)} />
      </div>
    </section>
  );
}

function ResultPanel({ run }: { run: TaskRun }) {
  const summary =
    typeof run.result_json?.summary === "string"
      ? run.result_json.summary
      : run.error ?? "Result will appear when the run completes.";

  return (
    <section className="rounded-md border border-zinc-200 bg-white p-4">
      <div className="mb-3 flex items-center gap-2">
        <FileText size={17} className="text-blue-700" />
        <h3 className="text-sm font-semibold">Result</h3>
      </div>
      <p className="text-sm leading-6 text-zinc-700">{summary}</p>
    </section>
  );
}

function AuditTable({ run }: { run: TaskRun }) {
  const subtasks = run.subtasks ?? [];
  return (
    <section className="rounded-md border border-zinc-200 bg-white">
      <div className="flex h-12 items-center gap-2 border-b border-zinc-200 px-4">
        <SquareCode size={17} className="text-orange-700" />
        <h3 className="text-sm font-semibold">Audit Log</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left text-sm">
          <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
            <tr>
              <th className="px-4 py-3 font-medium">Step</th>
              <th className="px-4 py-3 font-medium">Agent</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Updated</th>
            </tr>
          </thead>
          <tbody>
            {subtasks.length === 0 ? (
              <tr>
                <td className="px-4 py-4 text-zinc-500" colSpan={4}>
                  No subtasks recorded yet.
                </td>
              </tr>
            ) : (
              subtasks.map((subtask) => (
                <tr className="border-t border-zinc-100" key={subtask.id}>
                  <td className="px-4 py-3 font-medium text-zinc-900">{subtask.title}</td>
                  <td className="px-4 py-3 text-zinc-600">{subtask.agent_name}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={subtask.status} />
                  </td>
                  <td className="px-4 py-3 text-zinc-500">{formatTime(subtask.updated_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="mt-1 text-sm font-semibold text-zinc-900">{value}</div>
    </div>
  );
}

function shortId(id: string) {
  return id.slice(0, 8);
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export default App;
