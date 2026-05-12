export type AgentStatus =
  | "idle"
  | "working"
  | "error"
  | "offline"

export type TaskStatus =
  | "created"
  | "queued"
  | "assigned"
  | "in_progress"
  | "review"
  | "completed"
  | "failed"
  | "blocked"

export type Agent = {
  id: string
  name: string
  role: string
  department: string
  personality?: string
  position_x: number
  position_y: number
  current_action: string
  status: AgentStatus
  task_progress: number
  current_task_id?: string | null
  memory?: string[]
  last_update?: number
}

export type Department = {
  id: string
  name: string
  description: string
  manager_agent_id?: string | null
  agents: string[]
}

export type Task = {
  id: string
  title: string
  description: string
  department: string
  priority: string
  status: TaskStatus
  progress: number
  assigned_to?: string | null
  created_at: number
  updated_at?: number
  assigned_at?: number | null
  completed_at?: number | null
  result?: string | null
}

export type Event = {
  type: string
  payload?: Record<string, unknown>
  ts?: number
}

export type WorldState = {
  agents: Record<string, Agent>
  departments: Record<string, Department>
  tasks: Record<string, Task>
  events: Array<string | Event | Record<string, unknown>>
}
