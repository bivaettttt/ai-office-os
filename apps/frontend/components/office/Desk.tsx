interface DeskProps {
  x: number
  y: number
}

export default function Desk({ x, y }: DeskProps) {
  return (
    <div
      className="absolute"
      style={{
        left: `${x}px`,
        top: `${y}px`,
      }}
    >
      <div className="relative h-20 w-28 rounded-xl bg-[#7b5a3c] shadow-2xl border border-[#5f4228]">

        {/* MONITOR */}
        <div className="absolute left-7 top-3 h-8 w-14 rounded-md bg-neutral-900 border border-neutral-700">
          <div className="h-full w-full rounded-md bg-gradient-to-b from-cyan-400/30 to-blue-500/10" />
        </div>

        {/* KEYBOARD */}
        <div className="absolute left-8 top-14 h-2 w-12 rounded bg-neutral-200/80" />
      </div>
    </div>
  )
}