'use client'

import useAgentMotion from './useAgentMotion'

type Props = {
  name: string
  role: string

  action: string
  status: string

  x: number
  y: number
}

const roleColors: Record<string, string> = {
  ceo: '#22c55e',
  backend: '#22d3ee',
  frontend: '#38bdf8',
  ml: '#a855f7',
  research: '#f59e0b',
}

export default function AgentSprite({
  name,
  role,
  action,
  status,
  x,
  y,
}: Props) {
  const color =
    roleColors[role.toLowerCase()] || '#22d3ee'

  const position =
    useAgentMotion(x, y)

  return (
    <div
      className="
        absolute
        transition-all
        duration-[1400ms]
        ease-linear
        z-30
      "
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      {/* GLOW */}

      <div
        className="
          absolute
          left-1/2
          top-[18px]
          w-10
          h-10
          rounded-full
          blur-xl
          opacity-30
          -translate-x-1/2
        "
        style={{
          background: color,
        }}
      />

      {/* CHARACTER */}

      <div
        className="
          relative
          w-[34px]
          h-[44px]
          transition-transform
          duration-300
        "
      >
        {/* HEAD */}

        <div
          className="
            absolute
            left-[8px]
            top-0
            w-[18px]
            h-[18px]
            rounded-md
            border
          "
          style={{
            background: color,
            borderColor: 'rgba(255,255,255,0.5)',
            boxShadow: `0 0 12px ${color}`,
          }}
        />

        {/* BODY */}

        <div
          className="
            absolute
            left-[6px]
            top-[16px]
            w-[22px]
            h-[16px]
            rounded-sm
            border
          "
          style={{
            background: 'rgba(15,23,42,0.95)',
            borderColor: `${color}99`,
          }}
        />

        {/* LEGS */}

        <div
          className="
            absolute
            left-[9px]
            top-[31px]
            w-[5px]
            h-[11px]
            rounded-sm
            animate-pulse
          "
          style={{
            background: color,
          }}
        />

        <div
          className="
            absolute
            left-[20px]
            top-[31px]
            w-[5px]
            h-[11px]
            rounded-sm
            animate-pulse
          "
          style={{
            background: color,
          }}
        />

        {/* FACE */}

        <div className="absolute top-[3px] left-[11px] text-[8px] font-black text-black">
          {name.slice(0, 1)}
        </div>
      </div>

      {/* NAME */}

      <div
        className="
          absolute
          top-[48px]
          left-1/2
          -translate-x-1/2
          whitespace-nowrap
          text-[10px]
          font-bold
          tracking-wider
        "
        style={{
          color,
        }}
      >
        {name}
      </div>

      {/* ACTION */}

      <div
        className="
          absolute
          top-[-18px]
          left-1/2
          -translate-x-1/2
          whitespace-nowrap
          px-2
          py-1
          rounded-full
          text-[9px]
          font-bold
          border
          backdrop-blur-xl
        "
        style={{
          background: 'rgba(0,0,0,0.6)',
          borderColor: 'rgba(255,255,255,0.08)',
          color: '#cbd5e1',
        }}
      >
        {action}
      </div>

      {/* STATUS */}

      <div
        className={`
          absolute
          right-[-2px]
          top-[14px]
          w-2
          h-2
          rounded-full
          ${status === 'working' ? 'bg-green-400' : 'bg-zinc-500'}
        `}
      />
    </div>
  )
}
