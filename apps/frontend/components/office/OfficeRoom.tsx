type Agent = {
  id: string
  name: string
  role: string
  activity: string
  x: number
  y: number
}

type Desk = {
  x: number
  y: number
}

type Props = {
  title: string
  subtitle: string
  floor: string
  agents: Agent[]
  desks: Desk[]
}

export default function OfficeRoom({
  title,
  subtitle,
  floor,
  agents,
  desks,
}: Props) {
  return (
    <div
      className="
        relative
        h-full
        overflow-hidden
        rounded-[36px]
        border
        border-white/10
        shadow-2xl
      "
      style={{
        background: floor,
      }}
    >
      {/* LIGHTING */}

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.10),transparent_45%)]" />

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,rgba(0,255,255,0.08),transparent_40%)]" />

      {/* GRID */}

      <div
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px)
          `,
          backgroundSize: '40px 40px',
        }}
      />

      {/* HEADER */}

      <div className="absolute left-8 top-7 z-20">
        <div className="text-4xl font-black text-white drop-shadow-2xl">
          {title}
        </div>

        <div className="mt-2 text-sm tracking-wide text-white/60">
          {subtitle}
        </div>
      </div>

      {/* DESKS */}

      {desks.map((desk, i) => (
        <div
          key={i}
          className="
            absolute
            rounded-3xl
            border
            border-black/20
            shadow-2xl
          "
          style={{
            left: desk.x,
            top: desk.y,
            width: 150,
            height: 90,
            background:
              'linear-gradient(to bottom, #4b5563, #1f2937)',
          }}
        >
          {/* SCREEN */}

          <div
            className="
              absolute
              left-1/2
              top-3
              -translate-x-1/2
              rounded-xl
              border
              border-cyan-400/30
              bg-black
              shadow-[0_0_25px_rgba(0,255,255,0.35)]
            "
            style={{
              width: 64,
              height: 36,
            }}
          >
            <div className="h-full w-full rounded-xl bg-cyan-400/20" />
          </div>

          {/* CHAIR */}

          <div
            className="
              absolute
              left-1/2
              -bottom-7
              -translate-x-1/2
              rounded-full
              bg-neutral-900
            "
            style={{
              width: 46,
              height: 46,
            }}
          />
        </div>
      ))}

      {/* AGENTS */}

      {agents.map((agent) => (
        <div
          key={agent.id}
          className="absolute z-30"
          style={{
            left: agent.x,
            top: agent.y,
          }}
        >
          {/* AURA */}

          <div className="absolute left-1/2 top-1/2 h-24 w-24 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-400/20 blur-2xl" />

          {/* BODY */}

          <div
            className="
              relative
              flex
              h-16
              w-16
              items-center
              justify-center
              rounded-2xl
              border
              border-cyan-400/40
              bg-gradient-to-br
              from-cyan-400
              to-blue-600
              shadow-[0_0_30px_rgba(0,255,255,0.45)]
            "
          >
            <div className="h-5 w-5 rounded-full bg-white" />
          </div>

          {/* LABEL */}

          <div className="mt-3 text-center">
            <div className="text-sm font-bold text-white">
              {agent.name}
            </div>

            <div className="text-[11px] text-cyan-200">
              {agent.role}
            </div>
          </div>

          {/* ACTIVITY */}

          <div
            className="
              absolute
              -top-10
              left-1/2
              -translate-x-1/2
              whitespace-nowrap
              rounded-full
              border
              border-cyan-400/20
              bg-black/70
              px-3
              py-1
              text-[10px]
              text-cyan-300
              backdrop-blur-xl
            "
          >
            {agent.activity}
          </div>
        </div>
      ))}

      {/* AMBIENT GLOW */}

      <div className="pointer-events-none absolute inset-0 rounded-[36px] ring-1 ring-white/10" />
    </div>
  )
}