"use client"

import {
  useEffect,
  useRef,
  useState,
} from "react"
import { OfficeRendererEngine } from "@/engine"
import { frontendConfig } from "@/lib/config"
import type {
  ActivityFeedItem,
  RendererStats,
  SelectedAgentInfo,
} from "@/engine"
import { useWorldStore } from "@/store/useWorldStore"
import type {
  AgentActivityLogEntry,
  Task,
  TaskSummaryReasoningResponse,
  WorldState,
} from "@ai-office/types"

function selectWorldState(): WorldState {
  const state = useWorldStore.getState()

  return {
    agents: state.agents,
    departments: state.departments,
    tasks: state.tasks,
    events: state.events,
    activity_log: state.activity_log,
  }
}

export default function OfficeRendererCanvas() {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const engineRef =
    useRef<OfficeRendererEngine | null>(null)
  const eventCountRef = useRef(0)
  const [stats, setStats] =
    useState<RendererStats>({
      fps: 0,
      agentCount: 0,
      worldTick: 0,
      movingAgents: 0,
      selectedEntityId: null,
      currentActivity: "idle",
      renderMs: 0,
      activeTasks: 0,
      simulationSpeed: 1,
      paused: false,
    })
  const [selectedAgent, setSelectedAgent] =
    useState<SelectedAgentInfo | null>(null)
  const [activityFeed, setActivityFeed] =
    useState<ActivityFeedItem[]>([])
  const [selectedTaskId, setSelectedTaskId] =
    useState<string | null>(null)
  const [taskSummaryById, setTaskSummaryById] =
    useState<Record<string, TaskSummaryReasoningResponse>>({})
  const [taskSummaryLoadingId, setTaskSummaryLoadingId] =
    useState<string | null>(null)

  const socketConnected = useWorldStore(
    (state) => state.socketConnected
  )
  const tasks = useWorldStore(
    (state) => state.tasks
  )
  const agents = useWorldStore(
    (state) => state.agents
  )
  const departments = useWorldStore(
    (state) => state.departments
  )
  const activityLog = useWorldStore(
    (state) => state.activity_log || []
  )

  useEffect(() => {
    let disposed = false

    async function start() {
      if (!hostRef.current) {
        return
      }

      const engine = new OfficeRendererEngine({
        host: hostRef.current,
        onStats: setStats,
        onSelectAgent: setSelectedAgent,
        onActivity: (item) => {
          setActivityFeed((current) => [
            item,
            ...current,
          ].slice(0, 8))
        },
      })

      engineRef.current = engine
      await engine.init(selectWorldState())

      if (disposed) {
        engine.destroy()
      }
    }

    void start()

    const unsubscribe = useWorldStore.subscribe(
      (state) => {
        engineRef.current?.syncWorld({
          agents: state.agents,
          departments: state.departments,
          tasks: state.tasks,
          events: state.events,
          activity_log: state.activity_log,
        })

        if (state.events.length !== eventCountRef.current) {
          eventCountRef.current = state.events.length
          const latest = state.events
            .slice(-4)
            .reverse()
            .map((event, index) => ({
              id: `backend-${state.events.length}-${index}`,
              ts: Date.now(),
              message: eventToFeedText(event),
            }))

          setActivityFeed((current) => [
            ...latest,
            ...current.filter(
              (item) =>
                !item.id.startsWith("backend-")
            ),
          ].slice(0, 8))
        }
      }
    )

    return () => {
      disposed = true
      unsubscribe()
      engineRef.current?.destroy()
      engineRef.current = null
    }
  }, [])

  const selectedTask =
    selectedTaskId && tasks[selectedTaskId]
      ? tasks[selectedTaskId]
      : Object.values(tasks).find(
          (task) =>
            task.status !== "completed" &&
            task.status !== "cancelled"
        ) || null

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#0f1722]">
      <div
        ref={hostRef}
        className="absolute inset-0"
      />

      <div className="absolute left-3 top-3 z-10 grid grid-cols-2 gap-x-5 gap-y-1 border border-white/10 bg-black/65 px-3 py-2 text-[11px] font-mono text-white/80 backdrop-blur">
        <span>FPS</span>
        <span className="text-cyan-300">
          {stats.fps}
        </span>

        <span>Agents</span>
        <span className="text-cyan-300">
          {stats.agentCount}
        </span>

        <span>WS</span>
        <span
          className={
            socketConnected
              ? "text-green-400"
              : "text-red-400"
          }
        >
          {socketConnected ? "online" : "offline"}
        </span>

        <span>Tick</span>
        <span className="text-cyan-300">
          {stats.worldTick}
        </span>

        <span>Moving</span>
        <span className="text-cyan-300">
          {stats.movingAgents}
        </span>

        <span>Tasks</span>
        <span className="text-cyan-300">
          {stats.activeTasks}
        </span>

        <span>Activity</span>
        <span className="text-cyan-300">
          {stats.currentActivity}
        </span>

        <span>Selected</span>
        <span className="max-w-[90px] truncate text-cyan-300">
          {stats.selectedEntityId || "none"}
        </span>

        <span>Render</span>
        <span className="text-cyan-300">
          {stats.renderMs}ms
        </span>
      </div>

      <div className="absolute right-3 top-3 z-10 w-[270px] border border-white/10 bg-black/65 p-3 text-xs text-white/80 backdrop-blur">
        <div className="mb-2 text-sm font-semibold text-cyan-200">
          Office HUD
        </div>

        <div className="grid grid-cols-2 gap-y-1">
          <span className="text-white/50">
            Total agents
          </span>
          <span>{stats.agentCount}</span>

          <span className="text-white/50">
            Active tasks
          </span>
          <span>{stats.activeTasks}</span>

          <span className="text-white/50">
            Sim speed
          </span>
          <span>{stats.simulationSpeed}x</span>
        </div>

        <div className="mt-3 flex gap-2 border-t border-white/10 pt-3">
          <button
            type="button"
            onClick={() => {
              const next = !stats.paused
              engineRef.current?.setPaused(next)
              setStats((current) => ({
                ...current,
                paused: next,
              }))
            }}
            className="h-8 flex-1 bg-white/10 text-white"
          >
            {stats.paused ? "Resume" : "Pause"}
          </button>

          <button
            type="button"
            onClick={() => {
              const next =
                stats.simulationSpeed >= 2
                  ? 0.5
                  : stats.simulationSpeed + 0.5
              engineRef.current?.setSimulationSpeed(next)
              setStats((current) => ({
                ...current,
                simulationSpeed: next,
              }))
            }}
            className="h-8 flex-1 bg-white/10 text-white"
          >
            Speed
          </button>
        </div>

        <div className="mt-3 border-t border-white/10 pt-3">
          <div className="mb-2 font-semibold text-white">
            Departments
          </div>

          <DepartmentStatus />
        </div>

        <div className="mt-3 border-t border-white/10 pt-3">
          <div className="mb-2 font-semibold text-white">
            Task queue
          </div>

          <TaskList
            tasks={Object.values(tasks)}
            onSelect={setSelectedTaskId}
          />
        </div>

        <div className="mt-3 border-t border-white/10 pt-3">
          <div className="mb-2 font-semibold text-white">
            Activity feed
          </div>

          <div className="space-y-2">
            {activityFeed.length === 0 ? (
              <div className="text-white/40">
                Waiting for office activity
              </div>
            ) : (
              activityFeed.map((item) => (
                <div
                  key={item.id}
                  className="border-l border-cyan-300/50 pl-2 text-white/70"
                >
                  {item.message}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {selectedAgent && (
        <AgentDetails
          agent={selectedAgent}
          currentTask={
            selectedAgent.currentTaskId
              ? tasks[selectedAgent.currentTaskId]
              : undefined
          }
          activityLog={activityLog}
        />
      )}

      {selectedTask && (
        <TaskDetails
          task={selectedTask}
          onAction={(action) => {
            void controlTask(selectedTask.id, action)
          }}
          assignedAgentName={
            selectedTask.assigned_to
              ? agents[selectedTask.assigned_to]?.name
              : undefined
          }
          managerName={
            selectedTask.assigned_by_manager_id
              ? agents[
                  selectedTask.assigned_by_manager_id
                ]?.name
              : selectedTask.department
                ? agents[
                    Object.values(departments).find(
                      (department) =>
                        department.name ===
                        selectedTask.department
                    )?.manager_agent_id || ""
                  ]?.name
                : undefined
          }
          summary={taskSummaryById[selectedTask.id]}
          summaryLoading={
            taskSummaryLoadingId === selectedTask.id
          }
          onSummarize={() => {
            void summarizeTask(
              selectedTask.id,
              setTaskSummaryLoadingId,
              setTaskSummaryById
            )
          }}
        />
      )}
    </div>
  )
}

async function controlTask(
  taskId: string,
  action: "pause" | "resume" | "cancel" | "retry-step"
) {
  await fetch(
    `${frontendConfig.apiUrl}/tasks/${taskId}/${action}`,
    {
      method: "POST",
    }
  )
}

async function summarizeTask(
  taskId: string,
  setLoading: (value: string | null) => void,
  setSummaryById: (
    updater: (
      current: Record<
        string,
        TaskSummaryReasoningResponse
      >
    ) => Record<string, TaskSummaryReasoningResponse>
  ) => void
) {
  setLoading(taskId)
  try {
    const response = await fetch(
      `${frontendConfig.apiUrl}/llm/reasoning/task-summary`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ task_id: taskId }),
      }
    )
    const data = await response.json()
    if (!response.ok) {
      throw new Error(
        data.detail || "Summary request failed"
      )
    }
    setSummaryById((current) => ({
      ...current,
      [taskId]: data,
    }))
  } finally {
    setLoading(null)
  }
}

function AgentDetails({
  agent,
  currentTask,
  activityLog,
}: {
  agent: SelectedAgentInfo
  currentTask?: Task
  activityLog: AgentActivityLogEntry[]
}) {
  const activeStep =
    currentTask?.steps?.[
      currentTask.active_step_index || 0
    ]
  const recentActivity = activityLog
    .filter(
      (entry) =>
        entry.agent_id === agent.id ||
        entry.task_id === agent.currentTaskId
    )
    .slice(-3)
    .reverse()

  return (
    <div className="absolute bottom-3 left-3 z-10 w-[280px] border border-cyan-300/30 bg-black/70 p-4 text-sm text-white shadow-2xl backdrop-blur">
      <div className="text-lg font-semibold text-cyan-200">
        {agent.name}
        {agent.isManager && (
          <span className="ml-2 align-middle text-[10px] font-normal uppercase tracking-normal text-amber-200">
            manager
          </span>
        )}
      </div>

      <div className="mt-3 grid grid-cols-[96px_1fr] gap-y-2 text-xs">
        <span className="text-white/50">Role</span>
        <span>{agent.role}</span>

        <span className="text-white/50">
          Department
        </span>
        <span>{agent.department}</span>

        <span className="text-white/50">Status</span>
        <span>{agent.status}</span>

        <span className="text-white/50">Task</span>
        <span>
          {currentTask?.title || agent.currentTaskId || "none"}
        </span>

        <span className="text-white/50">Step</span>
        <span>
          {activeStep
            ? `${activeStep.title} · ${activeStep.progress}%`
            : "none"}
        </span>

        <span className="text-white/50">
          Capabilities
        </span>
        <span className="max-h-16 overflow-hidden text-[11px] text-white/75">
          {agent.capabilities?.join(", ") || "none"}
        </span>

        <span className="text-white/50">
          Position
        </span>
        <span>
          {agent.x}, {agent.y}
        </span>
      </div>

      <div className="mt-3 border-t border-white/10 pt-2 text-xs">
        <div className="mb-1 text-white/50">
          Recent activity
        </div>
        {recentActivity.length === 0 ? (
          <div className="text-white/35">none</div>
        ) : (
          recentActivity.map((entry) => (
            <div
              key={entry.id}
              className="truncate text-white/70"
            >
              {entry.message}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

function DepartmentStatus() {
  const agents = useWorldStore(
    (state) => state.agents
  )
  const tasks = useWorldStore(
    (state) => state.tasks
  )
  const departmentsById = useWorldStore(
    (state) => state.departments
  )

  const departments = [
    "development",
    "analytics",
    "assistant",
    "content",
    "operations",
  ]

  return (
    <div className="space-y-1">
      {departments.map((department) => {
        const count = Object.values(agents).filter(
          (agent) =>
            agent.department === department
        ).length
        const active = Object.values(tasks).filter(
          (task) =>
            task.department === department &&
            task.status !== "completed" &&
            task.status !== "failed" &&
            task.status !== "cancelled"
        ).length
        const idle = Object.values(agents).filter(
          (agent) =>
            agent.department === department &&
            agent.status === "idle"
        ).length
        const departmentModel = Object.values(
          departmentsById
        ).find((item) => item.name === department)
        const manager = departmentModel?.manager_agent_id
          ? agents[departmentModel.manager_agent_id]
          : Object.values(agents).find(
              (agent) =>
                agent.is_manager &&
                agent.manager_for_department ===
                  department
            )

        return (
          <div
            key={department}
            className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-0.5"
          >
            <span className="text-white/50">
              {department}
            </span>
            <span>
              {idle}/{count} idle · {active} tasks
            </span>
            {manager && (
              <span className="col-span-2 text-[10px] text-amber-200/80">
                manager: {manager.name}
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}

function TaskList({
  tasks,
  onSelect,
}: {
  tasks: Task[]
  onSelect: (id: string) => void
}) {
  const visibleTasks = tasks
    .slice()
    .sort(
      (a, b) =>
        (b.updated_at || b.created_at) -
        (a.updated_at || a.created_at)
    )
    .slice(0, 5)

  if (visibleTasks.length === 0) {
    return (
      <div className="text-white/40">
        No tasks queued
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {visibleTasks.map((task) => (
        <button
          type="button"
          key={task.id}
          onClick={() => onSelect(task.id)}
          className="block w-full border border-white/10 bg-white/5 p-2 text-left"
        >
          <div className="truncate text-white">
            {task.title}
          </div>
          <div className="mt-1 flex justify-between text-[11px] text-white/50">
            <span>{task.department}</span>
            <span>{task.status} · {task.progress}%</span>
          </div>
        </button>
      ))}
    </div>
  )
}

function TaskDetails({
  task,
  assignedAgentName,
  managerName,
  onAction,
  summary,
  summaryLoading,
  onSummarize,
}: {
  task: Task
  assignedAgentName?: string
  managerName?: string
  onAction: (
    action: "pause" | "resume" | "cancel" | "retry-step"
  ) => void
  summary?: TaskSummaryReasoningResponse
  summaryLoading: boolean
  onSummarize: () => void
}) {
  const phase = task.runtime_phase || task.status
  const canPause = phase === "executing"
  const canResume = phase === "paused"
  const canCancel = ![
    "completed",
    "failed",
    "cancelled",
  ].includes(phase)
  const canRetry =
    phase === "failed" &&
    Boolean(
      task.steps?.some(
        (step) => step.status === "failed"
      )
    )

  return (
    <div className="absolute bottom-3 right-3 z-10 w-[300px] border border-amber-300/30 bg-black/70 p-4 text-sm text-white shadow-2xl backdrop-blur">
      <div className="text-lg font-semibold text-amber-200">
        {task.title}
      </div>

      <div className="mt-3 grid grid-cols-[96px_1fr] gap-y-2 text-xs">
        <span className="text-white/50">Agent</span>
        <span>{assignedAgentName || "unassigned"}</span>

        <span className="text-white/50">Manager</span>
        <span>{managerName || "none"}</span>

        <span className="text-white/50">Status</span>
        <span>{task.status}</span>

        <span className="text-white/50">Phase</span>
        <span>{phase}</span>

        <span className="text-white/50">Progress</span>
        <span>{task.progress}%</span>

        <span className="text-white/50">Priority</span>
        <span>{task.priority}</span>

        <span className="text-white/50">Department</span>
        <span>{task.department}</span>

        <span className="text-white/50">
          Capabilities
        </span>
        <span className="max-h-16 overflow-hidden text-[11px] text-white/75">
          {task.required_capabilities?.join(", ") || "none"}
        </span>

        <span className="text-white/50">Created</span>
        <span>{new Date(task.created_at * 1000).toLocaleTimeString()}</span>

        <span className="text-white/50">Reviewed</span>
        <span>
          {task.reviewed_at
            ? new Date(task.reviewed_at * 1000)
                .toLocaleTimeString()
            : "none"}
        </span>

        <span className="text-white/50">Completed</span>
        <span>
          {task.completed_at
            ? new Date(task.completed_at * 1000)
                .toLocaleTimeString()
            : "none"}
        </span>
      </div>

      {task.failure_reason && (
        <div className="mt-3 border-t border-red-300/20 pt-3 text-xs text-red-200">
          {task.failure_reason}
        </div>
      )}

      <div className="mt-3 grid grid-cols-2 gap-2 border-t border-white/10 pt-3 text-xs">
        <TaskActionButton
          disabled={!canPause}
          onClick={() => onAction("pause")}
        >
          Pause
        </TaskActionButton>
        <TaskActionButton
          disabled={!canResume}
          onClick={() => onAction("resume")}
        >
          Resume
        </TaskActionButton>
        <TaskActionButton
          disabled={!canCancel}
          onClick={() => onAction("cancel")}
        >
          Cancel
        </TaskActionButton>
        <TaskActionButton
          disabled={!canRetry}
          onClick={() => onAction("retry-step")}
        >
          Retry step
        </TaskActionButton>
      </div>

      <div className="mt-3 border-t border-white/10 pt-3 text-xs">
        <button
          type="button"
          onClick={onSummarize}
          disabled={summaryLoading}
          className="w-full border border-white/10 bg-white/5 px-3 py-2 text-left text-cyan-200 disabled:opacity-50"
        >
          {summaryLoading
            ? "Generating AI summary..."
            : "AI task summary"}
        </button>
        {summary && (
          <div className="mt-2 rounded border border-white/10 bg-black/20 p-2 text-white/70">
            <div className="mb-1 text-[11px] text-cyan-200">
              {summary.provider_used}
              {summary.fallback_used
                ? " · fallback"
                : ""}
            </div>
            <div>{summary.summary}</div>
            {summary.current_state && (
              <div className="mt-1 text-white/55">
                state: {summary.current_state}
              </div>
            )}
            {summary.next_best_action && (
              <div className="mt-1 text-white/55">
                next: {summary.next_best_action}
              </div>
            )}
            {summary.safety_flags.length > 0 && (
              <div className="mt-1 text-amber-200">
                {summary.safety_flags.join(", ")}
              </div>
            )}
            {summary.fallback_reason && (
              <div className="mt-1 text-white/45">
                reason: {summary.fallback_reason}
              </div>
            )}
          </div>
        )}
      </div>

      {task.steps && task.steps.length > 0 && (
        <div className="mt-3 border-t border-white/10 pt-3 text-xs">
          <div className="mb-2 font-semibold text-white">
            Plan
          </div>
          <div className="space-y-1">
            {task.steps.map((step, index) => (
              <div
                key={step.id}
                className={
                  index ===
                  (task.active_step_index || 0)
                    ? "text-amber-100"
                    : "text-white/65"
                }
              >
                <div className="flex justify-between gap-2">
                  <span className="truncate">
                    {step.title}
                  </span>
                  <span>{step.progress}%</span>
                </div>
                <div className="text-[10px] text-white/40">
                  {step.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {task.result_summary && (
        <div className="mt-3 border-t border-white/10 pt-3 text-xs text-white/70">
          {task.result_summary}
        </div>
      )}
    </div>
  )
}

function TaskActionButton({
  children,
  disabled,
  onClick,
}: {
  children: string
  disabled: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="h-7 bg-white/10 px-2 text-white disabled:cursor-not-allowed disabled:opacity-35"
    >
      {children}
    </button>
  )
}

function eventToFeedText(
  event: string | Record<string, unknown>
) {
  if (typeof event === "string") {
    return event
  }

  const type =
    "type" in event && typeof event.type === "string"
      ? event.type
      : "event"
  const payload =
    "payload" in event &&
    event.payload &&
    typeof event.payload === "object"
      ? event.payload as Record<string, unknown>
      : {}

  if (type === "task.assigned") {
    return `${payload.agent_name || "Agent"} assigned ${payload.task_title || "task"}`
  }

  if (type === "task.started") {
    return `${payload.agent_name || "Agent"} started ${payload.task_title || "task"}`
  }

  if (type === "task.step_started") {
    return `${payload.agent_name || "Agent"} started ${payload.step_title || "step"}`
  }

  if (type === "task.step_completed") {
    return `${payload.agent_name || "Agent"} completed ${payload.step_title || "step"}`
  }

  if (type === "task.reviewed") {
    return `Manager reviewed ${payload.task_title || "task"}`
  }

  if (type === "task.paused") {
    return `Paused ${payload.task_title || "task"}`
  }

  if (type === "task.resumed") {
    return `Resumed ${payload.task_title || "task"}`
  }

  if (type === "task.cancelled") {
    return `Cancelled ${payload.task_title || "task"}`
  }

  if (type === "task.step_failed") {
    return `${payload.agent_name || "Agent"} failed ${payload.step_title || "step"}`
  }

  if (type === "task.retry_started") {
    return `Retry started: ${payload.step_title || "step"}`
  }

  if (type === "manager_selected_task") {
    return `${payload.manager_name || "Manager"} selected ${payload.task_title || "task"}`
  }

  if (type === "manager_assigned_worker") {
    return `${payload.manager_name || "Manager"} assigned ${payload.agent_name || "agent"}`
  }

  if (type === "capability_match_found") {
    return `Capability match found: ${payload.agent_name || "agent"}`
  }

  if (type === "capability_fallback_used") {
    return `Capability fallback used: ${payload.agent_name || "agent"}`
  }

  if (type === "no_capable_agent_available") {
    return `No capable agent available in ${payload.department || "department"}`
  }

  if (type === "task.completed") {
    return `${payload.agent || "Agent"} completed ${payload.task || "task"}`
  }

  if (type === "task.no_free_agents") {
    return `No free agents in ${payload.department || "department"}`
  }

  if (type === "task.queue_overloaded") {
    return "Task queue overloaded"
  }

  if (type === "command_received") {
    return "Command received"
  }

  if (type === "command_routed") {
    return `Command routed to ${payload.department || "department"}`
  }

  if (type === "command_task_created") {
    return `Command created ${payload.task_title || "task"}`
  }

  if (type === "command_failed") {
    return "Command failed"
  }

  return type
}
