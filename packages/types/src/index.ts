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
  active_permission_grants?: number
  expired_permission_grants?: number
  revoked_permission_grants?: number
  invocations_allowed_by_grant?: number
  pending_approvals_by_risk?: PendingApprovalsByRisk
  approvals_approved_total?: number
  approvals_rejected_total?: number
  dry_run_invocations_total?: number
  sandbox_contracts_created?: number
  llm_requests_total?: number
  llm_requests_failed?: number
  llm_provider_active?: string
  llm_real_calls_enabled?: boolean
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

export type PolicyProfile =
  | "locked_down"
  | "safe_local"
  | "assisted"
  | "autonomous_safe"

export type ToolPolicyProfile = PolicyProfile

export type PermissionScopeType =
  | "once"
  | "agent"
  | "department"
  | "task"
  | "global"

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
  used_grant_ids?: string[]
  profile?: PolicyProfile
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
  policy_profile?: PolicyProfile
  used_grant_ids?: string[]
  approval_expires_at?: number | null
  department?: string | null
  sandbox_contract_id?: string | null
  dry_run?: boolean
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
  profile?: PolicyProfile | null
  grant_ids?: string[]
  scope?: Record<string, unknown> | null
  reason?: string | null
}

export type PermissionGrant = {
  id: string
  scope_type: PermissionScopeType
  scope_id?: string | null
  permission: Permission
  tool_id?: string | null
  risk_level_max?: RiskLevel | null
  granted_by: string
  reason: string
  expires_at?: number | null
  created_at: number
  revoked_at?: number | null
  active: boolean
}

export type ApprovalScopeSuggestion = {
  scope_type: PermissionScopeType
  scope_id?: string | null
  permissions: Permission[]
  tool_id: string
  recommended_duration_minutes: number
  risk_warning: string
}

export type ApprovalRiskSummary = {
  risk_level: RiskLevel
  required_permissions: Permission[]
  policy_reason?: string | null
}

export type PendingApprovalsByRisk = {
  low: number
  medium: number
  high: number
  critical: number
}

export type SandboxContract = {
  id: string
  tool_id: string
  category: ToolCategory
  allowed_operations: string[]
  denied_operations: string[]
  required_permissions: Permission[]
  filesystem_scope?: Record<string, unknown> | null
  network_scope?: Record<string, unknown> | null
  timeout_seconds: number
  max_output_size: number
  requires_dry_run: boolean
  created_at: number
}

export type ToolExecutionRequest = {
  invocation_id: string
  tool_id: string
  arguments: Record<string, unknown>
  sandbox_contract_id: string
  dry_run: boolean
  agent_id?: string | null
  task_id?: string | null
}

export type ToolExecutionResult = {
  invocation_id: string
  status: string
  output?: Record<string, unknown> | null
  error?: string | null
  dry_run: boolean
  side_effects_declared: string[]
  side_effects_performed: string[]
  started_at: number
  completed_at?: number | null
}

export type ApprovalDetail = {
  invocation: ToolInvocation
  tool?: ToolDefinition | null
  policy_decision?: ToolPolicyDecision | null
  required_permissions: Permission[]
  risk_level?: RiskLevel | null
  related_task?: Task | null
  related_agent?: Agent | null
  related_department?: string | null
  audit_trail: ToolAuditEntry[]
  suggested_approval_scopes: ApprovalScopeSuggestion[]
  grants_used?: PermissionGrant[]
  policy_profile?: PolicyProfile
  policy_profile_description?: string
  sandbox_contract?: SandboxContract | null
  timeline?: RuntimeTimelineEntry[]
}

export type LLMSafetyFlag =
  | "empty_prompt_blocked"
  | "prompt_too_long_blocked"
  | "secret_redacted"
  | "tool_execution_blocked"
  | "real_calls_disabled"
  | "provider_fallback_used"

export type LLMMessage = {
  role: "system" | "user" | "assistant" | "tool"
  content: string
  name?: string | null
}

export type LLMRequest = {
  messages: LLMMessage[]
  model?: string | null
  temperature: number
  max_tokens?: number | null
  purpose: string
  task_id?: string | null
  agent_id?: string | null
  command_id?: string | null
  metadata?: Record<string, unknown>
}

export type LLMResponse = {
  content: string
  provider: string
  model: string
  usage?: Record<string, unknown> | null
  finish_reason?: string | null
  safety_flags: LLMSafetyFlag[]
  created_at: number
}

export type LLMProviderStatus = {
  name: string
  available: boolean
  model?: string | null
  reason?: string | null
}

export type LLMStatusResponse = {
  selected_provider: string
  active_provider: string
  real_calls_enabled: boolean
  providers: LLMProviderStatus[]
  model_config: Record<string, unknown>
  prompt_log_enabled: boolean
}

export type LLMPromptLogEntry = {
  id: string
  timestamp: number
  provider: string
  model: string
  purpose: string
  task_id?: string | null
  agent_id?: string | null
  command_id?: string | null
  prompt_preview: string
  response_preview: string
  safety_flags: LLMSafetyFlag[]
  status: string
  error?: string | null
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
  permission_grants?: Record<string, PermissionGrant>
  sandbox_contracts?: Record<string, SandboxContract>
  llm_prompt_logs?: LLMPromptLogEntry[]
}
