"use client"

import { useState } from "react"

import { frontendConfig } from "@/lib/config"
import { useWorldStore } from "@/store/useWorldStore"
import type {
  Task,
  UserCommand,
} from "@ai-office/types"

type CommandResponse = {
  command: UserCommand
  created_task: Task
  routing_explanation: string
}

const examples = [
  "сделай лендинг для кофейни",
  "проанализируй рынок онлайн-школ",
  "напомни мне завтра купить билеты",
  "напиши пост для Telegram",
]

export default function CommandCenter() {
  const [text, setText] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] =
    useState<CommandResponse | null>(null)
  const commands = useWorldStore(
    (state) => state.commands || {}
  )

  async function sendCommand() {
    if (!text.trim()) {
      return
    }

    setLoading(true)

    try {
      const response = await fetch(
        `${frontendConfig.apiUrl}/commands`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text,
          }),
        }
      )

      const data = await response.json()
      setResult(data)
      setText("")
    } finally {
      setLoading(false)
    }
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

      <button
        type="button"
        onClick={sendCommand}
        disabled={loading || !text.trim()}
        className="mt-3 h-10 w-full rounded-xl bg-cyan-500 font-bold text-black transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Routing..." : "Send command"}
      </button>

      <div className="mt-3 grid gap-2">
        {examples.map((example) => (
          <button
            type="button"
            key={example}
            onClick={() => setText(example)}
            className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-left text-xs text-white/65"
          >
            {example}
          </button>
        ))}
      </div>

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
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
