"use client"

import {
  useEffect,
  useState,
} from "react"

import { frontendConfig } from "@/lib/config"
import type {
  DepartmentRuntimeMetrics,
  RuntimeMetrics,
  RuntimeTimelineEntry,
  RuntimeTimelineResponse,
} from "@ai-office/types"

export default function ExecutionDashboard() {
  const [metrics, setMetrics] =
    useState<RuntimeMetrics | null>(null)
  const [department, setDepartment] =
    useState("all")
  const [timelineFilter, setTimelineFilter] =
    useState("all")
  const [timeline, setTimeline] =
    useState<RuntimeTimelineResponse | null>(null)
  const [debugJson, setDebugJson] =
    useState("")

  useEffect(() => {
    let disposed = false

    async function loadMetrics() {
      const [metricsResponse, timelineResponse] =
        await Promise.all([
          fetch(`${frontendConfig.apiUrl}/runtime/metrics`),
          fetch(
            `${frontendConfig.apiUrl}/runtime/timeline?limit=50`
          ),
        ])
      const data = await metricsResponse.json()
      const timelineData =
        await timelineResponse.json()

      if (!disposed) {
        setMetrics(data)
        setTimeline(timelineData)
      }
    }

    void loadMetrics()
    const timer = window.setInterval(
      loadMetrics,
      5000
    )

    return () => {
      disposed = true
      window.clearInterval(timer)
    }
  }, [])

  if (!metrics) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/50">
        Loading runtime metrics
      </div>
    )
  }

  const departments =
    metrics.department_metrics
  const visibleDepartments =
    department === "all"
      ? departments
      : departments.filter(
          (item) => item.department === department
        )
  const visibleAgents =
    department === "all"
      ? metrics.agent_workload
      : metrics.agent_workload.filter(
          (agent) => agent.department === department
        )

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-xs text-white/80">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="text-2xl">
          Execution
        </div>
        <span
          className={`rounded px-2 py-1 text-[10px] uppercase ${healthClass(
            metrics.queue_health
          )}`}
        >
          {metrics.queue_health}
        </span>
      </div>

      <select
        value={department}
        onChange={(event) =>
          setDepartment(event.target.value)
        }
        className="mb-3 h-8 w-full rounded border border-white/10 bg-[#111827] px-2 text-white outline-none"
      >
        <option value="all">All departments</option>
        {departments.map((item) => (
          <option
            key={item.department}
            value={item.department}
          >
            {item.department}
          </option>
        ))}
      </select>

      <GlobalSummary metrics={metrics} />

      <div className="mt-4 border-t border-white/10 pt-3">
        <div className="mb-2 font-semibold">
          Departments
        </div>
        <div className="space-y-2">
          {visibleDepartments.map((item) => (
            <DepartmentCard
              key={item.department}
              item={item}
            />
          ))}
        </div>
      </div>

      <div className="mt-4 border-t border-white/10 pt-3">
        <div className="mb-2 font-semibold">
          Agents
        </div>
        <div className="max-h-56 space-y-2 overflow-auto">
          {visibleAgents.map((agent) => (
            <div
              key={agent.id}
              className="border border-white/10 bg-black/20 p-2"
            >
              <div className="flex justify-between gap-2">
                <span className="truncate text-white">
                  {agent.name}
                </span>
                <span>{agent.status}</span>
              </div>
              <div className="truncate text-white/45">
                {agent.role} · {agent.department}
              </div>
              <div className="truncate text-white/55">
                {agent.current_task_title || "idle"}
              </div>
            </div>
          ))}
        </div>
      </div>

      <LogSection
        title="Manager decisions"
        entries={metrics.recent_manager_decisions}
      />

      <LogSection
        title="Failures"
        entries={metrics.recent_failures}
      />

      <TimelineSection
        entries={timeline?.entries || []}
        filter={timelineFilter}
        onFilter={setTimelineFilter}
        onDebug={setDebugJson}
      />

      {debugJson && (
        <textarea
          readOnly
          value={debugJson}
          className="mt-3 h-32 w-full resize-none border border-white/10 bg-black/40 p-2 font-mono text-[10px] text-white/70"
        />
      )}
    </div>
  )
}

function GlobalSummary({
  metrics,
}: {
  metrics: RuntimeMetrics
}) {
  const global = metrics.global_metrics

  return (
    <div className="grid grid-cols-2 gap-2">
      <SummaryCard
        label="Queued"
        value={global.queued_tasks}
      />
      <SummaryCard
        label="Running"
        value={global.in_progress_tasks}
      />
      <SummaryCard
        label="Failed"
        value={global.failed_tasks}
      />
      <SummaryCard
        label="Avg progress"
        value={`${global.average_task_progress}%`}
      />
      <SummaryCard
        label="Busy agents"
        value={global.busy_agents}
      />
      <SummaryCard
        label="Managers"
        value={global.managers_count}
      />
    </div>
  )
}

function SummaryCard({
  label,
  value,
}: {
  label: string
  value: string | number
}) {
  return (
    <div className="border border-white/10 bg-black/20 p-2">
      <div className="text-white/45">
        {label}
      </div>
      <div className="text-lg text-cyan-300">
        {value}
      </div>
    </div>
  )
}

function DepartmentCard({
  item,
}: {
  item: DepartmentRuntimeMetrics
}) {
  return (
    <div className="border border-white/10 bg-black/20 p-2">
      <div className="flex justify-between">
        <span className="text-white">
          {item.department}
        </span>
        <span>{item.workload_score}</span>
      </div>
      <div className="mt-1 text-white/50">
        {item.busy_agents}/{item.total_agents} busy ·{" "}
        {item.queued_tasks} queued ·{" "}
        {item.failed_tasks} failed
      </div>
    </div>
  )
}

function LogSection({
  title,
  entries,
}: {
  title: string
  entries: Array<{
    type: string
    message?: string
    payload?: Record<string, unknown>
  }>
}) {
  return (
    <div className="mt-4 border-t border-white/10 pt-3">
      <div className="mb-2 font-semibold">
        {title}
      </div>
      {entries.length === 0 ? (
        <div className="text-white/35">none</div>
      ) : (
        <div className="max-h-36 space-y-2 overflow-auto">
          {entries.map((entry, index) => (
            <div
              key={`${entry.type}-${index}`}
              className="border-l border-cyan-300/40 pl-2 text-white/60"
            >
              {entry.message ||
                String(
                  entry.payload?.task_title ||
                    entry.payload?.agent_name ||
                    entry.type
                )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function healthClass(health: string) {
  if (health === "healthy") {
    return "bg-green-400/15 text-green-300"
  }
  if (health === "busy") {
    return "bg-cyan-400/15 text-cyan-300"
  }
  if (health === "overloaded") {
    return "bg-amber-400/15 text-amber-300"
  }
  return "bg-red-400/15 text-red-300"
}

function TimelineSection({
  entries,
  filter,
  onFilter,
  onDebug,
}: {
  entries: RuntimeTimelineEntry[]
  filter: string
  onFilter: (value: string) => void
  onDebug: (value: string) => void
}) {
  const filtered = entries.filter((entry) => {
    if (filter === "errors") {
      return entry.severity === "error"
    }
    if (filter === "all") {
      return true
    }
    return entry.source_type === filter
  })

  async function copyDebugJson() {
    const json = JSON.stringify(
      filtered.slice(0, 50),
      null,
      2
    )

    try {
      await navigator.clipboard.writeText(json)
    } catch {
      onDebug(json)
      return
    }

    onDebug(json)
  }

  return (
    <div className="mt-4 border-t border-white/10 pt-3">
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="font-semibold">
          Timeline
        </div>
        <button
          type="button"
          onClick={copyDebugJson}
          className="bg-white/10 px-2 py-1 text-[10px] text-white"
        >
          Copy debug JSON
        </button>
      </div>

      <div className="mb-2 grid grid-cols-5 gap-1 text-[10px]">
        {["all", "task", "command", "manager", "errors"].map(
          (item) => (
            <button
              type="button"
              key={item}
              onClick={() => onFilter(item)}
              className={
                filter === item
                  ? "bg-cyan-400/20 text-cyan-200"
                  : "bg-white/10 text-white/55"
              }
            >
              {item}
            </button>
          )
        )}
      </div>

      <div className="max-h-64 space-y-2 overflow-auto">
        {filtered.slice(0, 50).map((entry) => (
          <div
            key={entry.id}
            className="border border-white/10 bg-black/20 p-2"
          >
            <div className="flex justify-between gap-2">
              <span className="truncate text-white">
                {entry.title}
              </span>
              <span
                className={`shrink-0 ${severityClass(
                  entry.severity
                )}`}
              >
                {entry.severity}
              </span>
            </div>
            <div className="truncate text-white/55">
              {entry.message}
            </div>
            <div className="mt-1 text-[10px] text-white/35">
              {new Date(
                entry.timestamp * 1000
              ).toLocaleTimeString()}{" "}
              · {entry.source_type}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function severityClass(severity: string) {
  if (severity === "success") {
    return "text-green-300"
  }
  if (severity === "warning") {
    return "text-amber-300"
  }
  if (severity === "error") {
    return "text-red-300"
  }
  return "text-cyan-300"
}
