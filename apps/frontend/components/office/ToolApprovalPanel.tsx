"use client"

import {
  useEffect,
  useMemo,
  useState,
} from "react"

import { frontendConfig } from "@/lib/config"
import type {
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

  async function loadTools() {
    const [toolsResponse, invocationsResponse] =
      await Promise.all([
        fetch(`${frontendConfig.apiUrl}/tools`),
        fetch(
          `${frontendConfig.apiUrl}/tools/invocations`
        ),
      ])

    if (!toolsResponse.ok || !invocationsResponse.ok) {
      throw new Error("Failed to load tools")
    }

    setTools(await toolsResponse.json())
    setInvocations(await invocationsResponse.json())
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
      `${frontendConfig.apiUrl}/tools/invocations/${id}/approve`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          approved_by: "user",
        }),
      }
    )
    await loadTools()
  }

  async function reject(id: string) {
    await fetch(
      `${frontendConfig.apiUrl}/tools/invocations/${id}/reject`,
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
                onApprove={approve}
                onReject={reject}
              />
            ))}
          </div>
        )}
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

function InvocationCard({
  invocation,
  readonly = false,
  onApprove,
  onReject,
}: {
  invocation: ToolInvocation
  readonly?: boolean
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
          <div className="mt-2 grid grid-cols-2 gap-2">
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
