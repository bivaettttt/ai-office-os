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

export type TaskStepStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed"
  | "skipped"

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
  capabilities?: string[]
  workload?: number
  performance_score?: number
  last_active_at?: number
  is_manager?: boolean
  manager_for_department?: string | null
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

export type TaskStep = {
  id: string
  title: string
  description: string
  status: TaskStepStatus
  progress: number
  started_at?: number | null
  completed_at?: number | null
  assigned_agent_id?: string | null
}

export type Task = {
  id: string
  title: string
  description: string
  department: string
  priority: string
  status: TaskStatus
  progress: number
  plan?: string[]
  steps?: TaskStep[]
  active_step_index?: number
  assigned_to?: string | null
  assigned_by_manager_id?: string | null
  required_capabilities?: string[]
  created_at: number
  updated_at?: number
  assigned_at?: number | null
  started_at?: number | null
  completed_at?: number | null
  reviewed_at?: number | null
  result?: string | null
  result_summary?: string | null
  failure_reason?: string | null
}

export type Event = {
  type: string
  payload?: Record<string, unknown>
  ts?: number
}

export type AgentActivityLogEntry = {
  id: string
  timestamp: number
  agent_id?: string | null
  task_id?: string | null
  type:
    | "task_assigned"
    | "step_started"
    | "step_completed"
    | "task_reviewed"
    | "task_completed"
    | "task_failed"
    | string
  message: string
}

export type WorldState = {
  agents: Record<string, Agent>
  departments: Record<string, Department>
  tasks: Record<string, Task>
  events: Array<string | Event | Record<string, unknown>>
  activity_log?: AgentActivityLogEntry[]
}
