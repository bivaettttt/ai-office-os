"use client"

import { useState } from "react"

import { frontendConfig } from "@/lib/config"
import { useWorldStore } from "@/store/useWorldStore"
import type {
  CommandPreview,
  Task,
  UserCommand,
} from "@ai-office/types"

type CommandResponse = {
  command: UserCommand
  created_task: Task
  routing_explanation: string
}

type PreviewResponse = {
  preview: CommandPreview
}

const examples = [
  "сделай лендинг для кофейни",
  "проанализируй рынок онлайн-школ",
  "напомни мне завтра купить билеты",
  "напиши пост для Telegram",
]

const departments = [
  "development",
  "analytics",
  "assistant",
  "content",
  "operations",
]

const priorities = ["low", "normal", "high"]

export default function CommandCenter() {
  const [text, setText] = useState("")
  const [department, setDepartment] = useState("")
  const [priority, setPriority] = useState("")
  const [title, setTitle] = useState("")
  const [description, setDescription] = useState("")
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] =
    useState<CommandPreview | null>(null)
  const [result, setResult] =
    useState<CommandResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const commands = useWorldStore(
    (state) => state.commands || {}
  )

  async function previewCommand() {
    if (!text.trim()) {
      setError("Command text is required")
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${frontendConfig.apiUrl}/commands/preview`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload()),
        }
      )
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Preview failed")
      }

      const next = (data as PreviewResponse).preview
      setPreview(next)
      setTitle(next.proposed_title)
      setDescription(next.proposed_description)
      setDepartment(next.inferred_department)
      setPriority(next.inferred_priority)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Preview failed"
      )
    } finally {
      setLoading(false)
    }
  }

  async function createTask() {
    if (!text.trim()) {
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `${frontendConfig.apiUrl}/commands`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload()),
        }
      )
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.detail || "Command failed")
      }

      setResult(data)
      setText("")
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Command failed"
      )
    } finally {
      setLoading(false)
    }
  }

  function payload() {
    return {
      text,
      department: department || undefined,
      priority: priority || undefined,
      title: title || undefined,
      description: description || undefined,
    }
  }

  function retryAsPreview(command: UserCommand) {
    setText(command.raw_text)
    setDepartment(
      command.inferred_department || ""
    )
    setPriority(command.inferred_priority || "")
    setTitle("")
    setDescription("")
    setError(command.error_message || null)
    setPreview(null)
  }

  const recent = Object.values(commands)
    .sort((a, b) => b.created_at - a.created_at)
    .slice(0, 5)

  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <div className="mb-3 text-2xl">
        Command Center
      </div>

      <textarea
        value={text}
        onChange={(event) =>
          setText(event.target.value)
        }
        placeholder="Напиши команду для AI Office"
        className="h-24 w-full resize-none rounded-xl border border-white/10 bg-[#111827] px-3 py-2 text-sm text-white outline-none"
      />

      <div className="mt-3 grid grid-cols-2 gap-2">
        <select
          value={department}
          onChange={(event) =>
            setDepartment(event.target.value)
          }
          className="h-9 rounded-lg border border-white/10 bg-[#111827] px-2 text-xs text-white outline-none"
        >
          <option value="">Auto department</option>
          {departments.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>

        <select
          value={priority}
          onChange={(event) =>
            setPriority(event.target.value)
          }
          className="h-9 rounded-lg border border-white/10 bg-[#111827] px-2 text-xs text-white outline-none"
        >
          <option value="">Auto priority</option>
          {priorities.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <button
          type="button"
          onClick={previewCommand}
          disabled={loading || !text.trim()}
          className="h-10 rounded-xl bg-white/10 font-bold text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Routing..." : "Preview"}
        </button>

        <button
          type="button"
          onClick={createTask}
          disabled={loading || !preview}
          className="h-10 rounded-xl bg-cyan-500 font-bold text-black transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Create Task
        </button>
      </div>

      <div className="mt-3 grid gap-2">
        {examples.map((example) => (
          <button
            type="button"
            key={example}
            onClick={() => {
              setText(example)
              setPreview(null)
              setResult(null)
            }}
            className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-left text-xs text-white/65"
          >
            {example}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-3 rounded-lg border border-red-400/20 bg-red-500/10 p-2 text-xs text-red-200">
          {error}
        </div>
      )}

      {preview && (
        <PreviewCard
          preview={preview}
          title={title}
          description={description}
          onTitle={setTitle}
          onDescription={setDescription}
        />
      )}

      {result && (
        <div className="mt-4 rounded-xl border border-green-500/20 bg-green-500/10 p-3 text-xs text-white/80">
          <div>
            Command: {result.command.status}
          </div>
          <div>
            Task: {result.created_task.title}
          </div>
          <div>
            Department: {result.created_task.department}
          </div>
          <CommandTimeline command={result.command} />
          <div className="mt-2 text-white/60">
            {result.routing_explanation}
          </div>
        </div>
      )}

      <div className="mt-4 border-t border-white/10 pt-3">
        <div className="mb-2 text-sm text-white/70">
          Recent commands
        </div>
        {recent.length === 0 ? (
          <div className="text-xs text-white/35">
            No commands yet
          </div>
        ) : (
          <div className="space-y-2">
            {recent.map((command) => (
              <div
                key={command.id}
                className="border-l border-cyan-300/40 pl-2 text-xs"
              >
                <div className="truncate text-white/75">
                  {command.raw_text}
                </div>
                <div className="text-white/40">
                  {command.status} ·{" "}
                  {command.inferred_department || "none"}
                </div>
                <CommandTimeline command={command} />
                {command.status === "failed" && (
                  <button
                    type="button"
                    onClick={() =>
                      retryAsPreview(command)
                    }
                    className="mt-1 text-cyan-300"
                  >
                    Retry as preview
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function PreviewCard({
  preview,
  title,
  description,
  onTitle,
  onDescription,
}: {
  preview: CommandPreview
  title: string
  description: string
  onTitle: (value: string) => void
  onDescription: (value: string) => void
}) {
  const providerLabel =
    preview.llm_provider_used &&
    preview.llm_provider_used !== "rules"
      ? preview.llm_provider_used
      : "rules"

  return (
    <div className="mt-4 rounded-xl border border-cyan-300/20 bg-cyan-500/10 p-3 text-xs text-white/80">
      <div className="grid grid-cols-[78px_1fr] gap-y-1">
        <span className="text-white/45">Dept</span>
        <span>{preview.inferred_department}</span>
        <span className="text-white/45">Priority</span>
        <span>{preview.inferred_priority}</span>
        <span className="text-white/45">Confidence</span>
        <span>
          {Math.round(preview.confidence_score * 100)}%
        </span>
        <span className="text-white/45">Caps</span>
        <span>
          {preview.inferred_capabilities.join(", ")}
        </span>
        <span className="text-white/45">LLM</span>
        <span>
          {providerLabel}
          {preview.llm_fallback_used
            ? " · fallback"
            : ""}
        </span>
      </div>

      {preview.warnings.length > 0 && (
        <div className="mt-2 space-y-1 text-amber-200">
          {preview.warnings.map((warning) => (
            <div key={warning.code}>
              {warning.message}
            </div>
          ))}
        </div>
      )}

      <input
        value={title}
        onChange={(event) =>
          onTitle(event.target.value)
        }
        className="mt-3 h-9 w-full rounded-lg border border-white/10 bg-[#111827] px-2 text-white outline-none"
      />
      <textarea
        value={description}
        onChange={(event) =>
          onDescription(event.target.value)
        }
        className="mt-2 h-16 w-full resize-none rounded-lg border border-white/10 bg-[#111827] px-2 py-1 text-white outline-none"
      />

      <div className="mt-2 text-white/55">
        {preview.routing_explanation}
      </div>

      {(preview.ai_explanation ||
        preview.ai_improved_title ||
        preview.ai_improved_description ||
        preview.ai_plan_notes) && (
        <div className="mt-3 border-t border-white/10 pt-2">
          <div className="mb-1 flex items-center justify-between gap-2 text-white/60">
            <span>AI reasoning</span>
            <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] text-cyan-200">
              {providerLabel}
            </span>
          </div>

          {preview.ai_explanation && (
            <div className="text-white/75">
              {preview.ai_explanation}
            </div>
          )}

          {preview.ai_improved_title && (
            <div className="mt-2">
              <div className="text-white/45">
                Suggested title
              </div>
              <div className="text-white/75">
                {preview.ai_improved_title}
              </div>
            </div>
          )}

          {preview.ai_improved_description && (
            <div className="mt-2">
              <div className="text-white/45">
                Suggested description
              </div>
              <div className="text-white/75">
                {preview.ai_improved_description}
              </div>
            </div>
          )}

          {preview.ai_plan_notes && (
            <div className="mt-2 text-white/65">
              {preview.ai_plan_notes}
            </div>
          )}

          {preview.llm_safety_flags &&
            preview.llm_safety_flags.length > 0 && (
              <div className="mt-2 text-[11px] text-amber-200">
                {preview.llm_safety_flags.join(", ")}
              </div>
            )}
        </div>
      )}

      <div className="mt-3 border-t border-white/10 pt-2">
        <div className="mb-1 text-white/60">
          Proposed plan
        </div>
        <div className="space-y-1">
          {preview.proposed_steps.map((step) => (
            <div key={step.id} className="truncate">
              {step.title}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function CommandTimeline({
  command,
}: {
  command: UserCommand
}) {
  const steps = [
    "received",
    "parsed",
    "routed",
    "task_created",
    "failed",
  ]

  return (
    <div className="mt-1 flex flex-wrap gap-1 text-[10px]">
      {steps.map((step) => (
        <span
          key={step}
          className={
            command.status === step
              ? "text-cyan-200"
              : "text-white/30"
          }
        >
          {step}
        </span>
      ))}
    </div>
  )
}
