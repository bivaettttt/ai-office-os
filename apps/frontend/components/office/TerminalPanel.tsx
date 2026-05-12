'use client'

import { useEffect, useState } from 'react'

const logs = [
  'Initializing AI workers...',
  'Running market analysis...',
  'Deploying backend agents...',
  'Syncing neural memory...',
  'Generating strategic report...',
  'Training prediction models...',
  'Monitoring infrastructure...',
  'Optimizing task routing...',
]

type Props = {
  x: number
  y: number

  width?: number
}

export default function TerminalPanel({
  x,
  y,
  width = 340,
}: Props) {
  const [items, setItems] = useState<string[]>([])

  useEffect(() => {
    const interval = setInterval(() => {
      setItems((prev) => {
        const next = logs[Math.floor(Math.random() * logs.length)]

        return [...prev.slice(-5), next]
      })
    }, 1400)

    return () => clearInterval(interval)
  }, [])

  return (
    <div
      className="absolute rounded-[24px] border overflow-hidden backdrop-blur-xl"
      style={{
        left: x,
        top: y,
        width,
        background: 'rgba(2,6,23,0.72)',
        borderColor: 'rgba(34,211,238,0.18)',
        boxShadow: '0 0 40px rgba(34,211,238,0.12)',
      }}
    >
      {/* HEADER */}

      <div className="flex items-center justify-between px-5 py-3 border-b border-white/10">
        <div className="text-cyan-300 text-sm font-black tracking-[0.25em]">
          AI TERMINAL
        </div>

        <div className="flex gap-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400" />
          <div className="w-2 h-2 rounded-full bg-violet-400" />
          <div className="w-2 h-2 rounded-full bg-emerald-400" />
        </div>
      </div>

      {/* BODY */}

      <div className="p-5 flex flex-col gap-2 min-h-[180px] font-mono text-xs">
        {items.map((item, index) => (
          <div
            key={`${item}-${index}`}
            className="text-cyan-200 opacity-90"
          >
            &gt; {item}
          </div>
        ))}
      </div>
    </div>
  )
}
