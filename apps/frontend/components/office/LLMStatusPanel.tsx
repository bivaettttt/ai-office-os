"use client"

import {
  useCallback,
  useEffect,
  useState,
} from "react"

import { frontendConfig } from "@/lib/config"
import type {
  LLMPromptLogEntry,
  LLMReasoningDiagnostics,
  LLMReasoningStatus,
  LLMResponse,
  LLMSuggestionReviewQueueResponse,
  LLMStatusResponse,
} from "@ai-office/types"

export default function LLMStatusPanel() {
  const [status, setStatus] =
    useState<LLMStatusResponse | null>(null)
  const [logs, setLogs] =
    useState<LLMPromptLogEntry[]>([])
  const [reasoningStatus, setReasoningStatus] =
    useState<LLMReasoningStatus | null>(null)
  const [diagnostics, setDiagnostics] =
    useState<LLMReasoningDiagnostics | null>(null)
  const [reviewQueue, setReviewQueue] =
    useState<LLMSuggestionReviewQueueResponse | null>(null)
  const [queueTypeFilter, setQueueTypeFilter] =
    useState("")
  const [queueDepartmentFilter, setQueueDepartmentFilter] =
    useState("")
  const [prompt, setPrompt] =
    useState("Summarize current office status")
  const [response, setResponse] =
    useState<LLMResponse | null>(null)
  const [error, setError] =
    useState("")

  const loadStatus = useCallback(async function loadStatus() {
    const [
      statusResponse,
      logsResponse,
      reasoningResponse,
      diagnosticsResponse,
      suggestionsResponse,
    ] =
      await Promise.all([
        fetch(`${frontendConfig.apiUrl}/llm/status`),
        fetch(`${frontendConfig.apiUrl}/llm/logs?limit=6`),
        fetch(`${frontendConfig.apiUrl}/llm/reasoning/status`),
        fetch(`${frontendConfig.apiUrl}/llm/reasoning/diagnostics`),
        fetch(
          `${frontendConfig.apiUrl}/llm/suggestions/review-queue?only_pending=true&limit=6${
            queueTypeFilter
              ? `&type=${encodeURIComponent(queueTypeFilter)}`
              : ""
          }${
            queueDepartmentFilter
              ? `&department=${encodeURIComponent(queueDepartmentFilter)}`
              : ""
          }`
        ),
      ])

    if (
      !statusResponse.ok ||
      !logsResponse.ok ||
      !reasoningResponse.ok ||
      !diagnosticsResponse.ok ||
      !suggestionsResponse.ok
    ) {
      throw new Error("Failed to load LLM status")
    }

    setStatus(await statusResponse.json())
    const logsData = await logsResponse.json()
    setLogs(logsData.items)
    setReasoningStatus(await reasoningResponse.json())
    setDiagnostics(await diagnosticsResponse.json())
    setReviewQueue(await suggestionsResponse.json())
  }, [queueDepartmentFilter, queueTypeFilter])

  useEffect(() => {
    let disposed = false

    async function refresh() {
      try {
        await loadStatus()
        if (!disposed) {
          setError("")
        }
      } catch (err) {
        if (!disposed) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load LLM status"
          )
        }
      }
    }

    void refresh()
    const timer = window.setInterval(
      refresh,
      8000
    )

    return () => {
      disposed = true
      window.clearInterval(timer)
    }
  }, [loadStatus])

  async function runTest() {
    setError("")
    const testResponse = await fetch(
      `${frontendConfig.apiUrl}/llm/test`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
        }),
      }
    )

    const data = await testResponse.json()
    if (!testResponse.ok) {
      setError(data.detail?.error || "LLM test failed")
      return
    }

    setResponse(data.response)
    await loadStatus()
  }

  async function reviewSuggestion(
    suggestionId: string,
    action: "approve" | "reject" | "apply"
  ) {
    await fetch(
      `${frontendConfig.apiUrl}/llm/suggestions/${suggestionId}/${action}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          reviewed_by: "manager-ui",
        }),
      }
    )
    await loadStatus()
  }

  async function promoteSuggestion(
    suggestionId: string
  ) {
    const response = await fetch(
      `${frontendConfig.apiUrl}/llm/suggestions/${suggestionId}/promote-command-draft`,
      { method: "POST" }
    )
    const data = await response.json()
    if (!response.ok) {
      setError(data.detail || "Failed to promote draft")
      return
    }
    window.dispatchEvent(
      new CustomEvent("ai-office:promoted-command-draft", {
        detail: data,
      })
    )
    await loadStatus()
  }

  async function bulkExpirePending() {
    await fetch(
      `${frontendConfig.apiUrl}/llm/suggestions/bulk-expire`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      }
    )
    await loadStatus()
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-xs text-white/80">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="text-2xl">
          LLM
        </div>
        <span className="rounded bg-cyan-400/10 px-2 py-1 text-[10px] text-cyan-200">
          {status?.active_provider || "loading"}
        </span>
      </div>

      {status && (
        <div className="mb-3 space-y-1 text-white/55">
          <div>selected: {status.selected_provider}</div>
          <div>
            real calls:{" "}
            {status.real_calls_enabled ? "enabled" : "disabled"}
          </div>
          <div>
            prompt log:{" "}
            {status.prompt_log_enabled ? "enabled" : "disabled"}
          </div>
          <div>
            reasoning:{" "}
            {reasoningStatus?.reasoning_enabled
              ? "enabled"
              : "disabled"}
          </div>
          {diagnostics && (
            <>
              <div>
                fallbacks: {diagnostics.recent_fallbacks_count}
              </div>
              <div>
                rate limited:{" "}
                {diagnostics.recent_rate_limited_count}
              </div>
              <div>
                schema failures:{" "}
                {diagnostics.recent_schema_failures_count}
              </div>
            </>
          )}
        </div>
      )}

      {diagnostics && (
        <div className="mb-3 rounded border border-white/10 bg-black/20 p-2 text-[11px] text-white/60">
          <div>
            cache: {diagnostics.cache_size}
          </div>
          <div>
            limit/min: {diagnostics.rate_limit_settings.per_minute}
          </div>
          <div>
            limit/purpose: {diagnostics.rate_limit_settings.per_purpose}
          </div>
          <div>
            cache ttl: {diagnostics.rate_limit_settings.cache_ttl_seconds}s
          </div>
        </div>
      )}

      <div className="mb-3 space-y-2">
        {status?.providers.map((provider) => (
          <div
            key={provider.name}
            className="border border-white/10 bg-black/20 p-2"
          >
            <div className="flex justify-between gap-2">
              <span>{provider.name}</span>
              <span
                className={
                  provider.available
                    ? "text-green-300"
                    : "text-amber-300"
                }
              >
                {provider.available ? "available" : "unavailable"}
              </span>
            </div>
            <div className="truncate text-white/35">
              {provider.model || "no model"} ·{" "}
              {provider.reason || "ready"}
            </div>
          </div>
        ))}
      </div>

      <textarea
        value={prompt}
        onChange={(event) =>
          setPrompt(event.target.value)
        }
        className="h-20 w-full resize-none border border-white/10 bg-black/30 p-2 text-white outline-none"
      />
      <button
        type="button"
        onClick={runTest}
        className="mt-2 w-full bg-cyan-400/15 px-2 py-1 text-cyan-200"
      >
        Test prompt
      </button>

      {error && (
        <div className="mt-2 border border-red-400/30 bg-red-500/10 p-2 text-red-200">
          {error}
        </div>
      )}

      {response && (
        <div className="mt-2 border border-white/10 bg-black/20 p-2 text-white/65">
          <div className="text-cyan-200">
            {response.provider} · {response.model}
          </div>
          <div className="mt-1">
            {response.content}
          </div>
        </div>
      )}

      <div className="mt-4 border-t border-white/10 pt-3">
        <div className="mb-2 font-semibold">
          Review queue
        </div>
        <div className="mb-2 grid grid-cols-2 gap-2">
          <select
            value={queueTypeFilter}
            onChange={(event) =>
              setQueueTypeFilter(event.target.value)
            }
            className="border border-white/10 bg-black/20 px-2 py-1 text-[11px] text-white"
          >
            <option value="">all types</option>
            <option value="command_preview">command_preview</option>
            <option value="task_plan">task_plan</option>
            <option value="manager_review">manager_review</option>
            <option value="task_summary">task_summary</option>
            <option value="timeline_summary">timeline_summary</option>
          </select>
          <select
            value={queueDepartmentFilter}
            onChange={(event) =>
              setQueueDepartmentFilter(event.target.value)
            }
            className="border border-white/10 bg-black/20 px-2 py-1 text-[11px] text-white"
          >
            <option value="">all departments</option>
            <option value="development">development</option>
            <option value="analytics">analytics</option>
            <option value="assistant">assistant</option>
            <option value="content">content</option>
            <option value="operations">operations</option>
          </select>
        </div>
        {reviewQueue && (
          <div className="mb-2 rounded border border-white/10 bg-black/20 p-2 text-[11px] text-white/60">
            <div>
              pending: {reviewQueue.counts_by_status.pending_review || 0}
            </div>
            <div>
              oldest pending: {reviewQueue.oldest_pending_age_seconds}s
            </div>
          </div>
        )}
        <button
          type="button"
          onClick={() => void bulkExpirePending()}
          className="mb-3 bg-white/10 px-2 py-1 text-[10px] text-white/75"
        >
          Bulk expire old pending
        </button>
        <div className="mb-4 max-h-44 space-y-2 overflow-auto">
          {!reviewQueue || reviewQueue.suggestions.length === 0 ? (
            <div className="text-white/35">none</div>
          ) : (
            reviewQueue.suggestions.map((item) => (
              <div
                key={item.suggestion.id}
                className="border border-white/10 bg-black/20 p-2"
              >
                <div className="flex justify-between gap-2">
                  <span>{item.suggestion.type}</span>
                  <span className="text-cyan-200">
                    {item.suggestion.source_provider}
                  </span>
                </div>
                <div className="truncate text-white/45">
                  {item.department || "unknown"} · {item.age_seconds}s
                </div>
                <div className="truncate text-white/65">
                  {item.suggestion.content}
                </div>
                <div className="mt-1 text-[10px] text-white/45">
                  {item.apply_effect_preview}
                </div>
                <div className="mt-2 flex gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      void reviewSuggestion(item.suggestion.id, "approve")
                    }
                    className="bg-green-400/15 px-2 py-1 text-[10px] text-green-200"
                  >
                    Approve
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      void reviewSuggestion(item.suggestion.id, "reject")
                    }
                    className="bg-red-400/15 px-2 py-1 text-[10px] text-red-200"
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      void reviewSuggestion(item.suggestion.id, "apply")
                    }
                    disabled={!item.can_apply}
                    className="bg-cyan-400/15 px-2 py-1 text-[10px] text-cyan-200"
                  >
                    Apply
                  </button>
                  {item.suggestion.type === "command_preview" && (
                    <button
                      type="button"
                      onClick={() =>
                        void promoteSuggestion(item.suggestion.id)
                      }
                      className="bg-amber-400/15 px-2 py-1 text-[10px] text-amber-200"
                    >
                      Promote draft
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="mb-2 font-semibold">
          Prompt logs
        </div>
        <div className="max-h-40 space-y-2 overflow-auto">
          {logs.map((log) => (
            <div
              key={log.id}
              className="border border-white/10 bg-black/20 p-2"
            >
              <div className="flex justify-between gap-2">
                <span>{log.provider}</span>
                <span>{log.status}</span>
              </div>
              <div className="truncate text-white/45">
                {log.prompt_preview}
              </div>
              <div className="truncate text-white/35">
                {log.response_preview || log.error || "no response"}
              </div>
              {log.safety_flags.length > 0 && (
                <div className="mt-1 truncate text-[10px] text-amber-200">
                  {log.safety_flags.join(", ")}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
