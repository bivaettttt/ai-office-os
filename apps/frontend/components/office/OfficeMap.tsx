'use client'

import OfficeRoom from './OfficeRoom'
import { useWorldStore } from '@/store/useWorldStore'


type Agent = {
  id: string
  name: string
  role: string
  department: string
  current_action: string
  position_x: number
  position_y: number
}


const waveformHeights = [
  12, 22, 18, 30, 42, 24, 36, 28, 18, 40,
  52, 32, 20, 14, 34, 48, 26, 38, 44, 24,
  18, 28, 36, 50, 30, 22, 14, 40, 48, 26,
  34, 18, 24, 42, 52, 30, 20, 16, 28, 36,
]

export default function OfficeMap() {
  
  const agents = useWorldStore(
    (state) => state.agents
  ) as Record<string, Agent>

  const developmentAgents = Object.values(agents)
    .filter((a) => a.department === 'dev')
    .map((a) => ({
      id: a.id,
      name: a.name,
      role: a.role,
      activity: a.current_action,
      x: a.position_x,
      y: a.position_y,
    }))

  const analyticsAgents = Object.values(agents)
    .filter((a) => a.department === 'analytics')
    .map((a) => ({
      id: a.id,
      name: a.name,
      role: a.role,
      activity: a.current_action,
      x: a.position_x,
      y: a.position_y,
    }))

  const assistantAgents = Object.values(agents)
    .filter((a) => a.department === 'assistant')
    .map((a) => ({
      id: a.id,
      name: a.name,
      role: a.role,
      activity: a.current_action,
      x: a.position_x,
      y: a.position_y,
    }))

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#050816] text-white">

      {/* BACKGROUND */}

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(0,255,255,0.08),transparent_35%)]" />

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,rgba(0,120,255,0.08),transparent_40%)]" />

      {/* GRID */}

      <div
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* FLOATING LIGHTS */}

      <div className="absolute left-[10%] top-[20%] h-72 w-72 rounded-full bg-cyan-500/10 blur-[140px]" />

      <div className="absolute right-[10%] top-[10%] h-96 w-96 rounded-full bg-blue-500/10 blur-[160px]" />

      <div className="absolute bottom-[5%] left-[40%] h-96 w-96 rounded-full bg-indigo-500/10 blur-[160px]" />

      {/* TOP BAR */}

      <div className="relative z-20 flex items-center justify-between border-b border-white/10 bg-black/40 px-8 py-6 backdrop-blur-2xl">

        <div>
          <div className="text-5xl font-black tracking-[0.28em] text-white">
            AI OFFICE HUB
          </div>

          <div className="mt-2 text-sm tracking-[0.45em] text-cyan-400">
            DIGITAL OPERATIONS CENTER
          </div>
        </div>

        <div className="flex items-center gap-12">

          <div>
            <div className="text-xs tracking-[0.25em] text-white/40">
              PRODUCTIVITY
            </div>

            <div className="mt-1 text-3xl font-black text-green-400">
              92%
            </div>
          </div>

          <div>
            <div className="text-xs tracking-[0.25em] text-white/40">
              AGENTS
            </div>

            <div className="mt-1 text-3xl font-black text-cyan-400">
              12
            </div>
          </div>

          <div>
            <div className="text-xs tracking-[0.25em] text-white/40">
              STATUS
            </div>

            <div className="mt-1 text-3xl font-black text-green-400">
              ONLINE
            </div>
          </div>
        </div>
      </div>

      {/* OFFICE GRID */}

      <div className="relative z-10 grid grid-cols-2 gap-8 p-8">

        <div className="h-[460px]">
          <OfficeRoom
            title="Отдел разработки"
            subtitle="AI software engineering department"
            floor="linear-gradient(to bottom, #7a5a3a, #3d2a1d)"
            agents={developmentAgents}
            desks={[
              { x: 70, y: 150 },
              { x: 250, y: 220 },
              { x: 430, y: 170 },
            ]}
          />
        </div>

        <div className="h-[460px]">
          <OfficeRoom
            title="Отдел аналитики"
            subtitle="AI research and intelligence department"
            floor="linear-gradient(to bottom, #2c3f5f, #162235)"
            agents={analyticsAgents}
            desks={[
              { x: 90, y: 180 },
              { x: 300, y: 240 },
            ]}
          />
        </div>

        <div className="col-span-2 h-[420px]">
          <OfficeRoom
            title="Отдел личных дел"
            subtitle="Personal AI assistant department"
            floor="linear-gradient(to bottom, #66523b, #35291f)"
            agents={assistantAgents}
            desks={[
              { x: 130, y: 170 },
              { x: 390, y: 240 },
            ]}
          />
        </div>
      </div>

      {/* EVA PANEL */}

      <div
        className="
          fixed
          bottom-8
          right-8
          z-50
          w-[420px]
          overflow-hidden
          rounded-[36px]
          border
          border-cyan-400/20
          bg-black/50
          p-6
          shadow-[0_0_80px_rgba(0,255,255,0.15)]
          backdrop-blur-2xl
        "
      >
        {/* GLOW */}

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(0,255,255,0.12),transparent_45%)]" />

        <div className="relative z-10">

          <div className="flex items-center gap-5">

            {/* AVATAR */}

            <div
              className="
                flex
                h-24
                w-24
                items-center
                justify-center
                rounded-3xl
                bg-gradient-to-br
                from-cyan-400
                to-blue-700
                text-4xl
                shadow-[0_0_40px_rgba(0,255,255,0.45)]
              "
            >
              🤖
            </div>

            <div>
              <div className="text-3xl font-black text-white">
                Eva Assistant
              </div>

              <div className="mt-2 text-sm text-green-400">
                Neural systems operational...
              </div>
            </div>
          </div>

          {/* WAVEFORM */}

          <div className="mt-8 flex h-16 items-end gap-1">
            {waveformHeights.map((height, i) => (
              <div
                key={i}
                className="w-1 rounded-full bg-cyan-400 shadow-[0_0_10px_rgba(0,255,255,0.8)]"
                style={{
                  height: `${height}px`,
                }}
              />
            ))}
          </div>

          {/* BUTTONS */}

          <div className="mt-8 flex gap-3">

            <button
              className="
                rounded-2xl
                bg-cyan-400
                px-6
                py-3
                font-bold
                text-black
                transition-all
                hover:scale-105
                hover:bg-cyan-300
              "
            >
              Speak
            </button>

            <button
              className="
                rounded-2xl
                border
                border-white/10
                bg-white/5
                px-6
                py-3
                font-medium
                text-white
                backdrop-blur-xl
                transition-all
                hover:bg-white/10
              "
            >
              Create Task
            </button>

            <button
              className="
                rounded-2xl
                border
                border-white/10
                bg-white/5
                px-6
                py-3
                font-medium
                text-white
                backdrop-blur-xl
                transition-all
                hover:bg-white/10
              "
            >
              Analytics
            </button>

          </div>
        </div>
      </div>
    </div>
  )
}