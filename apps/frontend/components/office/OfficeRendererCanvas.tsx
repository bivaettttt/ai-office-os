"use client"

import {
  useEffect,
  useRef,
  useState,
} from "react"
import { OfficeRendererEngine } from "@/engine"
import type {
  ActivityFeedItem,
  RendererStats,
  SelectedAgentInfo,
} from "@/engine"
import { useWorldStore } from "@/store/useWorldStore"
import type {
  Task,
  WorldState,
} from "@ai-office/types"

function selectWorldState(): WorldState {
  const state = useWorldStore.getState()

  return {
    agents: state.agents,
    departments: state.departments,
    tasks: state.tasks,
    events: state.events,
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

  const socketConnected = useWorldStore(
    (state) => state.socketConnected
  )
  const tasks = useWorldStore(
    (state) => state.tasks
  )
  const agents = useWorldStore(
    (state) => state.agents
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
            task.status === "in_progress" ||
            task.status === "assigned"
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
        <div className="absolute bottom-3 left-3 z-10 w-[280px] border border-cyan-300/30 bg-black/70 p-4 text-sm text-white shadow-2xl backdrop-blur">
          <div className="text-lg font-semibold text-cyan-200">
            {selectedAgent.name}
          </div>

          <div className="mt-3 grid grid-cols-[96px_1fr] gap-y-2 text-xs">
            <span className="text-white/50">Role</span>
            <span>{selectedAgent.role}</span>

            <span className="text-white/50">
              Department
            </span>
            <span>{selectedAgent.department}</span>

            <span className="text-white/50">
              Status
            </span>
            <span>{selectedAgent.status}</span>

            <span className="text-white/50">
              Task
            </span>
            <span>
              {selectedAgent.currentTaskId || "none"}
            </span>

            <span className="text-white/50">
              Position
            </span>
            <span>
              {selectedAgent.x}, {selectedAgent.y}
            </span>
          </div>
        </div>
      )}

      {selectedTask && (
        <TaskDetails
          task={selectedTask}
          assignedAgentName={
            selectedTask.assigned_to
              ? agents[selectedTask.assigned_to]?.name
              : undefined
          }
        />
      )}
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

  const departments = [
    "development",
    "analytics",
    "assistant",
    "content",
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
            task.status !== "failed"
        ).length
        const idle = Object.values(agents).filter(
          (agent) =>
            agent.department === department &&
            agent.status === "idle"
        ).length

        return (
          <div
            key={department}
            className="flex justify-between gap-3"
          >
            <span className="text-white/50">
              {department}
            </span>
            <span>
              {idle}/{count} idle · {active} tasks
            </span>
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
}: {
  task: Task
  assignedAgentName?: string
}) {
  return (
    <div className="absolute bottom-3 right-3 z-10 w-[300px] border border-amber-300/30 bg-black/70 p-4 text-sm text-white shadow-2xl backdrop-blur">
      <div className="text-lg font-semibold text-amber-200">
        {task.title}
      </div>

      <div className="mt-3 grid grid-cols-[96px_1fr] gap-y-2 text-xs">
        <span className="text-white/50">Agent</span>
        <span>{assignedAgentName || "unassigned"}</span>

        <span className="text-white/50">Status</span>
        <span>{task.status}</span>

        <span className="text-white/50">Progress</span>
        <span>{task.progress}%</span>

        <span className="text-white/50">Priority</span>
        <span>{task.priority}</span>

        <span className="text-white/50">Department</span>
        <span>{task.department}</span>

        <span className="text-white/50">Created</span>
        <span>{new Date(task.created_at * 1000).toLocaleTimeString()}</span>
      </div>
    </div>
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

  if (type === "task.completed") {
    return `${payload.agent || "Agent"} completed ${payload.task || "task"}`
  }

  if (type === "task.no_free_agents") {
    return `No free agents in ${payload.department || "department"}`
  }

  if (type === "task.queue_overloaded") {
    return "Task queue overloaded"
  }

  return type
}
