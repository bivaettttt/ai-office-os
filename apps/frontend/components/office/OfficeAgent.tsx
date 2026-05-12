interface OfficeAgentProps {
  name: string
  role: string
  activity: string
  x: number
  y: number
}

export default function OfficeAgent({
  name,
  role,
  activity,
  x,
  y,
}: OfficeAgentProps) {
  return (
    <div
      className="absolute transition-all duration-1000"
      style={{
        left: `${x}px`,
        top: `${y}px`,
      }}
    >
      <div className="relative flex flex-col items-center">

        {/* ACTIVITY */}
        <div className="mb-1 rounded-full border border-neutral-700 bg-neutral-900/95 px-2 py-1 text-[10px] text-cyan-300 shadow-lg">
          {activity}
        </div>

        {/* PIXEL CHARACTER */}
        <div className="relative h-10 w-8">

          {/* HEAD */}
          <div className="absolute left-2 top-0 h-4 w-4 rounded-sm bg-orange-200" />

          {/* BODY */}
          <div className="absolute left-[10px] top-4 h-4 w-3 bg-cyan-400" />

          {/* LEGS */}
          <div className="absolute left-[10px] top-8 h-2 w-1 bg-neutral-800" />
          <div className="absolute left-[12px] top-8 h-2 w-1 bg-neutral-800" />
        </div>

        {/* NAME */}
        <div className="mt-1 text-[11px] font-semibold text-cyan-300">
          {name}
        </div>

        {/* ROLE */}
        <div className="text-[10px] text-neutral-400">
          {role}
        </div>
      </div>
    </div>
  )
}