"use client"

import {
  useEffect,
  useMemo,
  useState,
} from "react"

import { frontendConfig } from "@/lib/config"
import type {
  ApprovalDetail,
  ApprovalScopeSuggestion,
  Permission,
  PermissionGrant,
  PermissionScopeType,
  PolicyProfile,
  ToolDefinition,
  ToolInvocation,
} from "@ai-office/types"

export default function ToolApprovalPanel() {
  const [tools, setTools] =
    useState<ToolDefinition[]>([])
  const [invocations, setInvocations] =
    useState<ToolInvocation[]>([])
  const [error, setError] =
    useState("")
  const [policyProfile, setPolicyProfile] =
    useState<PolicyProfile>("safe_local")
  const [grants, setGrants] =
    useState<PermissionGrant[]>([])
  const [approvals, setApprovals] =
    useState<ApprovalDetail[]>([])
  const [selectedApproval, setSelectedApproval] =
    useState<ApprovalDetail | null>(null)
  const [dryRunPreview, setDryRunPreview] =
    useState<Record<string, unknown> | null>(null)
  const [grantForm, setGrantForm] = useState({
    scope_type: "global" as PermissionScopeType,
    scope_id: "",
    permission: "create_report" as Permission,
    tool_id: "",
    expires_in_minutes: "60",
    reason: "Temporary local approval",
  })
  const [approveWithGrant, setApproveWithGrant] =
    useState(false)
  const [grantDuration, setGrantDuration] =
    useState("60")

  async function loadTools() {
    const [
      toolsResponse,
      invocationsResponse,
      grantsResponse,
      approvalsResponse,
    ] =
      await Promise.all([
        fetch(`${frontendConfig.apiUrl}/tools`),
        fetch(
          `${frontendConfig.apiUrl}/tools/invocations`
        ),
        fetch(`${frontendConfig.apiUrl}/tools/grants`),
        fetch(`${frontendConfig.apiUrl}/approvals`),
      ])

    if (
      !toolsResponse.ok ||
      !invocationsResponse.ok ||
      !grantsResponse.ok ||
      !approvalsResponse.ok
    ) {
      throw new Error("Failed to load tools")
    }

    setTools(await toolsResponse.json())
    setInvocations(await invocationsResponse.json())
    const grantsData = await grantsResponse.json()
    setPolicyProfile(grantsData.policy_profile)
    setGrants(grantsData.grants)
    const approvalsData = await approvalsResponse.json()
    setApprovals(approvalsData.items)
  }

  useEffect(() => {
    let disposed = false

    async function refresh() {
      try {
        await loadTools()
        if (!disposed) {
          setError("")
        }
      } catch (err) {
        if (!disposed) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load tools"
          )
        }
      }
    }

    void refresh()
    const timer = window.setInterval(
      refresh,
      5000
    )

    return () => {
      disposed = true
      window.clearInterval(timer)
    }
  }, [])

  const pending = useMemo(
    () =>
      invocations.filter(
        (invocation) =>
          invocation.status === "awaiting_approval"
      ),
    [invocations]
  )

  async function approve(id: string) {
    await fetch(
      `${frontendConfig.apiUrl}/approvals/${id}/approve`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          approved_by: "user",
          create_grant: approveWithGrant,
          grant_expires_in_minutes:
            approveWithGrant && grantDuration
              ? Number(grantDuration)
              : null,
        }),
      }
    )
    await loadTools()
  }

  async function reject(id: string) {
    await fetch(
      `${frontendConfig.apiUrl}/approvals/${id}/reject`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rejected_by: "user",
        }),
      }
    )
    await loadTools()
  }

  async function createGrant() {
    await fetch(`${frontendConfig.apiUrl}/tools/grants`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        scope_type: grantForm.scope_type,
        scope_id: grantForm.scope_id || null,
        permission: grantForm.permission,
        tool_id: grantForm.tool_id || null,
        expires_in_minutes: grantForm.expires_in_minutes
          ? Number(grantForm.expires_in_minutes)
          : null,
        reason: grantForm.reason,
      }),
    })
    await loadTools()
  }

  async function revokeGrant(id: string) {
    await fetch(
      `${frontendConfig.apiUrl}/tools/grants/${id}/revoke`,
      {
        method: "POST",
      }
    )
    await loadTools()
  }

  async function openApproval(id: string) {
    const response = await fetch(
      `${frontendConfig.apiUrl}/approvals/${id}`
    )
    setSelectedApproval(await response.json())
    setDryRunPreview(null)
  }

  async function dryRunApproval(detail: ApprovalDetail) {
    const response = await fetch(
      `${frontendConfig.apiUrl}/tools/invoke`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tool_id: detail.invocation.tool_id,
          task_id: detail.invocation.task_id,
          agent_id: detail.invocation.agent_id,
          department: detail.invocation.department,
          requested_by: "user",
          arguments: detail.invocation.arguments,
          dry_run: true,
        }),
      }
    )
    setDryRunPreview(await response.json())
    await loadTools()
  }

  async function approveScope(
    detail: ApprovalDetail,
    scope: ApprovalScopeSuggestion
  ) {
    await fetch(
      `${frontendConfig.apiUrl}/approvals/${detail.invocation.id}/approve`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          approved_by: "user",
          create_grant: scope.scope_type !== "once",
          grant_scope_type:
            scope.scope_type === "once"
              ? null
              : scope.scope_type,
          grant_scope_id: scope.scope_id || null,
          grant_expires_in_minutes:
            scope.recommended_duration_minutes || null,
        }),
      }
    )
    setSelectedApproval(null)
    setDryRunPreview(null)
    await loadTools()
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-xs text-white/80">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="text-2xl">
          Tools
        </div>
        <span className="rounded bg-amber-400/15 px-2 py-1 text-[10px] text-amber-200">
          {pending.length} approvals
        </span>
      </div>
      <div className="mb-3 rounded bg-cyan-400/10 px-2 py-1 text-[10px] text-cyan-200">
        profile: {policyProfile}
      </div>
      <div className="mb-3 border border-white/10 bg-black/20 p-2 text-[10px] text-white/55">
        {policyDescription(policyProfile)}
        <div className="mt-1">
          forbidden: shell, network, browser, secrets, system
        </div>
        <div>
          active grants: {grants.filter((grant) => grant.active).length} · pending:{" "}
          {approvals.length}
        </div>
      </div>

      {error && (
        <div className="mb-3 border border-red-400/30 bg-red-500/10 p-2 text-red-200">
          {error}
        </div>
      )}

      <section className="mb-4">
        <div className="mb-2 font-semibold">
          Registry
        </div>
        <div className="max-h-44 space-y-2 overflow-auto">
          {tools.map((tool) => (
            <div
              key={tool.id}
              className="border border-white/10 bg-black/20 p-2"
            >
              <div className="flex justify-between gap-2">
                <span className="truncate text-white">
                  {tool.name}
                </span>
                <span
                  className={`shrink-0 ${riskClass(
                    tool.risk_level
                  )}`}
                >
                  {tool.risk_level}
                </span>
              </div>
              <div className="truncate text-white/45">
                {tool.category} ·{" "}
                {tool.required_permissions.join(", ")}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-white/10 pt-3">
        <div className="mb-2 font-semibold">
          Pending approvals
        </div>
        {pending.length === 0 ? (
          <div className="text-white/35">
            none
          </div>
        ) : (
          <div className="space-y-2">
            {pending.map((invocation) => (
              <InvocationCard
                key={invocation.id}
                invocation={invocation}
                onOpen={openApproval}
                onApprove={approve}
                onReject={reject}
              />
            ))}
          </div>
        )}
        <label className="mt-3 flex items-center gap-2 text-white/55">
          <input
            type="checkbox"
            checked={approveWithGrant}
            onChange={(event) =>
              setApproveWithGrant(event.target.checked)
            }
          />
          Approve with temporary grant
        </label>
        <input
          value={grantDuration}
          onChange={(event) =>
            setGrantDuration(event.target.value)
          }
          className="mt-2 h-8 w-full border border-white/10 bg-black/30 px-2 text-white outline-none"
          placeholder="Grant minutes"
        />
      </section>

      {selectedApproval && (
        <ApprovalDetailCard
          detail={selectedApproval}
          dryRunPreview={dryRunPreview}
          onDryRun={dryRunApproval}
          onApproveScope={approveScope}
          onReject={reject}
        />
      )}

      <section className="mt-4 border-t border-white/10 pt-3">
        <div className="mb-2 font-semibold">
          Active grants
        </div>
        <GrantForm
          value={grantForm}
          onChange={setGrantForm}
          onCreate={createGrant}
        />
        <div className="mt-3 max-h-44 space-y-2 overflow-auto">
          {grants.map((grant) => (
            <div
              key={grant.id}
              className="border border-white/10 bg-black/20 p-2"
            >
              <div className="flex justify-between gap-2">
                <span className="truncate text-white">
                  {grant.permission}
                </span>
                <span
                  className={
                    grant.active
                      ? "text-green-300"
                      : "text-red-300"
                  }
                >
                  {grant.active ? "active" : "inactive"}
                </span>
              </div>
              <div className="truncate text-white/45">
                {grant.scope_type}:{grant.scope_id || "*"} ·{" "}
                {grant.tool_id || "any tool"}
              </div>
              {grant.active && !grant.revoked_at && (
                <button
                  type="button"
                  onClick={() => revokeGrant(grant.id)}
                  className="mt-2 bg-red-400/15 px-2 py-1 text-red-200"
                >
                  Revoke
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      <section className="mt-4 border-t border-white/10 pt-3">
        <div className="mb-2 font-semibold">
          Invocation history
        </div>
        <div className="max-h-48 space-y-2 overflow-auto">
          {invocations.slice(0, 8).map((invocation) => (
            <InvocationCard
              key={invocation.id}
              invocation={invocation}
              readonly
            />
          ))}
        </div>
      </section>
    </div>
  )
}

function GrantForm({
  value,
  onChange,
  onCreate,
}: {
  value: {
    scope_type: PermissionScopeType
    scope_id: string
    permission: Permission
    tool_id: string
    expires_in_minutes: string
    reason: string
  }
  onChange: (value: {
    scope_type: PermissionScopeType
    scope_id: string
    permission: Permission
    tool_id: string
    expires_in_minutes: string
    reason: string
  }) => void
  onCreate: () => Promise<void>
}) {
  return (
    <div className="grid gap-2">
      <select
        value={value.scope_type}
        onChange={(event) =>
          onChange({
            ...value,
            scope_type: event.target.value as PermissionScopeType,
          })
        }
        className="h-8 border border-white/10 bg-black/30 px-2 text-white"
      >
        {["global", "agent", "department", "task"].map(
          (scope) => (
            <option key={scope} value={scope}>
              {scope}
            </option>
          )
        )}
      </select>
      <input
        value={value.scope_id}
        onChange={(event) =>
          onChange({
            ...value,
            scope_id: event.target.value,
          })
        }
        className="h-8 border border-white/10 bg-black/30 px-2 text-white"
        placeholder="scope id optional"
      />
      <input
        value={value.permission}
        onChange={(event) =>
          onChange({
            ...value,
            permission: event.target.value as Permission,
          })
        }
        className="h-8 border border-white/10 bg-black/30 px-2 text-white"
        placeholder="permission"
      />
      <input
        value={value.tool_id}
        onChange={(event) =>
          onChange({
            ...value,
            tool_id: event.target.value,
          })
        }
        className="h-8 border border-white/10 bg-black/30 px-2 text-white"
        placeholder="tool id optional"
      />
      <input
        value={value.expires_in_minutes}
        onChange={(event) =>
          onChange({
            ...value,
            expires_in_minutes: event.target.value,
          })
        }
        className="h-8 border border-white/10 bg-black/30 px-2 text-white"
        placeholder="expires in minutes"
      />
      <input
        value={value.reason}
        onChange={(event) =>
          onChange({
            ...value,
            reason: event.target.value,
          })
        }
        className="h-8 border border-white/10 bg-black/30 px-2 text-white"
        placeholder="reason"
      />
      <button
        type="button"
        onClick={onCreate}
        className="bg-cyan-400/15 px-2 py-1 text-cyan-200"
      >
        Create grant
      </button>
    </div>
  )
}

function InvocationCard({
  invocation,
  readonly = false,
  onOpen,
  onApprove,
  onReject,
}: {
  invocation: ToolInvocation
  readonly?: boolean
  onOpen?: (id: string) => Promise<void>
  onApprove?: (id: string) => Promise<void>
  onReject?: (id: string) => Promise<void>
}) {
  return (
    <div className="border border-white/10 bg-black/20 p-2">
      <div className="flex justify-between gap-2">
        <span className="truncate text-white">
          {invocation.tool_id}
        </span>
        <span className={statusClass(invocation.status)}>
          {invocation.status}
        </span>
      </div>
      <div className="mt-1 truncate text-white/45">
        {invocation.policy_decision?.reason ||
          invocation.error ||
          "requested"}
      </div>
      {invocation.result && (
        <div className="mt-1 truncate text-green-200/70">
          {JSON.stringify(invocation.result)}
        </div>
      )}
      {!readonly &&
        invocation.status === "awaiting_approval" && (
          <div className="mt-2 grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => onOpen?.(invocation.id)}
              className="bg-cyan-400/15 px-2 py-1 text-cyan-200"
            >
              Detail
            </button>
            <button
              type="button"
              onClick={() => onApprove?.(invocation.id)}
              className="bg-green-400/15 px-2 py-1 text-green-200"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => onReject?.(invocation.id)}
              className="bg-red-400/15 px-2 py-1 text-red-200"
            >
              Reject
            </button>
          </div>
        )}
    </div>
  )
}

function ApprovalDetailCard({
  detail,
  dryRunPreview,
  onDryRun,
  onApproveScope,
  onReject,
}: {
  detail: ApprovalDetail
  dryRunPreview: Record<string, unknown> | null
  onDryRun: (detail: ApprovalDetail) => Promise<void>
  onApproveScope: (
    detail: ApprovalDetail,
    scope: ApprovalScopeSuggestion
  ) => Promise<void>
  onReject: (id: string) => Promise<void>
}) {
  return (
    <section className="mt-4 border-t border-white/10 pt-3">
      <div className="mb-2 font-semibold">
        Approval Center
      </div>
      <div className="border border-white/10 bg-black/20 p-2">
        <div className="flex justify-between gap-2">
          <span className="truncate text-white">
            {detail.tool?.name || detail.invocation.tool_id}
          </span>
          <span className={riskClass(detail.risk_level || "low")}>
            {detail.risk_level}
          </span>
        </div>
        <div className="mt-1 text-white/45">
          {detail.policy_decision?.reason}
        </div>
        <div className="mt-2 text-white/55">
          permissions: {detail.required_permissions.join(", ")}
        </div>
        {detail.sandbox_contract && (
          <div className="mt-2 text-white/45">
            sandbox: {detail.sandbox_contract.category} · denied{" "}
            {detail.sandbox_contract.denied_operations.length}
          </div>
        )}
        <div className="mt-2 grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => onDryRun(detail)}
            className="bg-cyan-400/15 px-2 py-1 text-cyan-200"
          >
            Dry-run preview
          </button>
          <button
            type="button"
            onClick={() => onReject(detail.invocation.id)}
            className="bg-red-400/15 px-2 py-1 text-red-200"
          >
            Reject
          </button>
        </div>
        <div className="mt-3 space-y-2">
          {detail.suggested_approval_scopes.map((scope) => (
            <button
              type="button"
              key={`${scope.scope_type}-${scope.scope_id || "none"}`}
              onClick={() => onApproveScope(detail, scope)}
              className="block w-full bg-green-400/10 px-2 py-1 text-left text-green-200"
            >
              {scope.scope_type} · {scope.recommended_duration_minutes}m
              <span className="block truncate text-[10px] text-white/40">
                {scope.risk_warning}
              </span>
            </button>
          ))}
        </div>
        <div className="mt-3 text-white/45">
          audit entries: {detail.audit_trail.length}
        </div>
        {dryRunPreview && (
          <pre className="mt-2 max-h-28 overflow-auto whitespace-pre-wrap border border-white/10 bg-black/40 p-2 text-[10px] text-white/60">
            {JSON.stringify(dryRunPreview, null, 2)}
          </pre>
        )}
      </div>
    </section>
  )
}

function policyDescription(profile: PolicyProfile) {
  if (profile === "locked_down") {
    return "All tools require approval; high and critical are blocked."
  }
  if (profile === "assisted") {
    return "Low runs locally; medium/high require approval."
  }
  if (profile === "autonomous_safe") {
    return "Low/medium require matching scoped grants."
  }
  return "Low runs locally; medium requires approval; high is blocked."
}

function riskClass(risk: string) {
  if (risk === "low") {
    return "text-green-300"
  }
  if (risk === "medium") {
    return "text-amber-300"
  }
  return "text-red-300"
}

function statusClass(status: string) {
  if (status === "completed") {
    return "text-green-300"
  }
  if (
    status === "blocked" ||
    status === "cancelled" ||
    status === "failed"
  ) {
    return "text-red-300"
  }
  if (status === "awaiting_approval") {
    return "text-amber-300"
  }
  return "text-cyan-300"
}
