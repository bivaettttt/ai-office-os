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
  | "cancelled"

export type TaskRuntimePhase =
  | "created"
  | "queued"
  | "assigned"
  | "planning"
  | "executing"
  | "reviewing"
  | "completed"
  | "failed"
  | "cancelled"
  | "paused"

export type TaskStepStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "failed"
  | "skipped"

export type CommandStatus =
  | "received"
  | "parsed"
  | "routed"
  | "task_created"
  | "failed"

export type UserCommand = {
  id: string
  raw_text: string
  normalized_text: string
  status: CommandStatus
  inferred_department?: string | null
  inferred_priority: string
  inferred_capabilities: string[]
  created_task_id?: string | null
  created_at: number
  processed_at?: number | null
  error_message?: string | null
}

export type CommandRouteResult = {
  department: string
  priority: string
  required_capabilities: string[]
  title: string
  description: string
  explanation: string
  matched_keywords: string[]
}

export type CommandValidationWarning = {
  code: string
  message: string
}

export type CommandConfidence = number

export type CommandPreview = {
  normalized_text: string
  inferred_department: string
  inferred_priority: string
  inferred_capabilities: string[]
  routing_explanation: string
  proposed_title: string
  proposed_description: string
  proposed_steps: TaskStep[]
  warnings: CommandValidationWarning[]
  confidence_score: CommandConfidence
  valid: boolean
}

export type CommandCreateRequest = {
  text: string
  department?: string | null
  priority?: string | null
  title?: string | null
  description?: string | null
}

export type QueueHealth =
  | "healthy"
  | "busy"
  | "overloaded"
  | "blocked"

export type RuntimeGlobalMetrics = {
  total_tasks: number
  queued_tasks: number
  in_progress_tasks: number
  completed_tasks: number
  failed_tasks: number
  cancelled_tasks: number
  paused_tasks: number
  total_agents: number
  busy_agents: number
  idle_agents: number
  managers_count: number
  average_task_progress: number
  active_commands: number
  failed_commands: number
  pending_tool_approvals?: number
  completed_tool_invocations?: number
  blocked_tool_invocations?: number
}

export type DepartmentRuntimeMetrics = {
  department: string
  total_agents: number
  busy_agents: number
  idle_agents: number
  managers: number
  queued_tasks: number
  in_progress_tasks: number
  completed_tasks: number
  failed_tasks: number
  workload_score: number
}

export type AgentWorkloadSummary = {
  id: string
  name: string
  role: string
  department: string
  status: AgentStatus
  current_task_id?: string | null
  current_task_title?: string | null
  workload: number
  performance_score: number
  capabilities: string[]
  recent_activity_count: number
}

export type ManagerDecisionEntry = {
  type: string
  payload?: Record<string, unknown>
  ts?: number
  timestamp?: number
  message?: string
  agent_id?: string | null
  task_id?: string | null
}

export type TimelineSeverity =
  | "info"
  | "success"
  | "warning"
  | "error"

export type TimelineSourceType =
  | "command"
  | "task"
  | "agent"
  | "manager"
  | "system"

export type RuntimeTimelineEntry = {
  id: string
  timestamp: number
  source_type: TimelineSourceType
  source_id: string
  event_type: string
  title: string
  message: string
  severity: TimelineSeverity
  related_task_id?: string | null
  related_command_id?: string | null
  related_agent_id?: string | null
  metadata?: Record<string, unknown>
}

export type RuntimeTimelineResponse = {
  entries: RuntimeTimelineEntry[]
  filters_applied: Record<string, unknown>
  total: number
}

export type TaskDrilldown = {
  task: Task
  command?: UserCommand | null
  assigned_agent?: Agent | null
  assigned_manager?: Agent | null
  timeline: RuntimeTimelineEntry[]
  steps: TaskStep[]
  activity_log: AgentActivityLogEntry[]
}

export type CommandDrilldown = {
  command: UserCommand
  created_task?: Task | null
  timeline: RuntimeTimelineEntry[]
  routing_explanation?: string | null
  activity_log: AgentActivityLogEntry[]
}

export type RuntimeMetrics = {
  global_metrics: RuntimeGlobalMetrics
  department_metrics: DepartmentRuntimeMetrics[]
  agent_workload: AgentWorkloadSummary[]
  recent_manager_decisions: ManagerDecisionEntry[]
  recent_failures: ManagerDecisionEntry[]
  queue_health: QueueHealth
}

export type Permission =
  | "read_project_files"
  | "write_project_files"
  | "run_tests"
  | "run_shell_command"
  | "access_network"
  | "access_browser"
  | "access_calendar"
  | "access_messaging"
  | "access_secrets"
  | "modify_system"
  | "create_report"
  | "generate_content"

export type RiskLevel =
  | "low"
  | "medium"
  | "high"
  | "critical"

export type ToolCategory =
  | "filesystem"
  | "terminal"
  | "browser"
  | "network"
  | "calendar"
  | "messaging"
  | "analysis"
  | "generation"
  | "system"

export type PolicyDecision =
  | "allowed"
  | "requires_approval"
  | "blocked"

export type ToolPolicyDecision = {
  decision: PolicyDecision
  reason: string
}

export type ToolInvocationStatus =
  | "requested"
  | "awaiting_approval"
  | "approved"
  | "running"
  | "completed"
  | "failed"
  | "blocked"
  | "cancelled"

export type ToolDefinition = {
  id: string
  name: string
  description: string
  category: ToolCategory
  required_capabilities: string[]
  required_permissions: Permission[]
  risk_level: RiskLevel
  enabled: boolean
  requires_approval: boolean
}

export type ToolInvocation = {
  id: string
  tool_id: string
  task_id?: string | null
  agent_id?: string | null
  requested_by: string
  arguments: Record<string, unknown>
  status: ToolInvocationStatus
  policy_decision?: ToolPolicyDecision | null
  approval_required: boolean
  approved_by?: string | null
  approved_at?: number | null
  result?: Record<string, unknown> | null
  error?: string | null
  created_at: number
  completed_at?: number | null
}

export type ToolAuditEntry = {
  id: string
  timestamp: number
  invocation_id: string
  tool_id: string
  task_id?: string | null
  agent_id?: string | null
  action: string
  decision?: PolicyDecision | null
  message: string
  risk_level: RiskLevel
  permissions: Permission[]
}

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
  runtime_phase?: TaskRuntimePhase
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
    | "task_paused"
    | "task_resumed"
    | "task_cancelled"
    | "step_failed"
    | "task_retry_requested"
    | "task_retry_started"
    | "manager_review_approved"
    | "manager_review_failed"
    | "command_received"
    | "command_parsed"
    | "command_routed"
    | "command_task_created"
    | "command_failed"
    | string
  message: string
}

export type WorldState = {
  agents: Record<string, Agent>
  departments: Record<string, Department>
  tasks: Record<string, Task>
  events: Array<string | Event | Record<string, unknown>>
  activity_log?: AgentActivityLogEntry[]
  commands?: Record<string, UserCommand>
  tool_invocations?: Record<string, ToolInvocation>
  tool_audit_log?: ToolAuditEntry[]
}
