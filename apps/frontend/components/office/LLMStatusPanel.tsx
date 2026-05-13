"use client"

import {
  useEffect,
  useState,
} from "react"

import { frontendConfig } from "@/lib/config"
import type {
  LLMPromptLogEntry,
  LLMReasoningDiagnostics,
  LLMReasoningStatus,
  LLMResponse,
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
  const [prompt, setPrompt] =
    useState("Summarize current office status")
  const [response, setResponse] =
    useState<LLMResponse | null>(null)
  const [error, setError] =
    useState("")

  async function loadStatus() {
    const [
      statusResponse,
      logsResponse,
      reasoningResponse,
      diagnosticsResponse,
    ] =
      await Promise.all([
        fetch(`${frontendConfig.apiUrl}/llm/status`),
        fetch(`${frontendConfig.apiUrl}/llm/logs?limit=6`),
        fetch(`${frontendConfig.apiUrl}/llm/reasoning/status`),
        fetch(`${frontendConfig.apiUrl}/llm/reasoning/diagnostics`),
      ])

    if (
      !statusResponse.ok ||
      !logsResponse.ok ||
      !reasoningResponse.ok ||
      !diagnosticsResponse.ok
    ) {
      throw new Error("Failed to load LLM status")
    }

    setStatus(await statusResponse.json())
    const logsData = await logsResponse.json()
    setLogs(logsData.items)
    setReasoningStatus(await reasoningResponse.json())
    setDiagnostics(await diagnosticsResponse.json())
  }

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
  }, [])

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
