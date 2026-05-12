type Props = {
  x: number
  y: number
}

export default function MeetingTable({
  x,
  y,
}: Props) {
  return (
    <div
      className="absolute"
      style={{
        left: x,
        top: y,
      }}
    >
      {/* TABLE */}

      <div
        className="
          relative
          rounded-xl
        "
        style={{
          width: 180,
          height: 90,

          background: '#d9d4cb',

          boxShadow: `
            0 10px 25px rgba(0,0,0,0.2)
          `,
        }}
      >
        {/* CHAIRS */}

        {[
          [12, 12],
          [12, 52],
          [142, 12],
          [142, 52],
        ].map(([cx, cy], i) => (
          <div
            key={i}
            className="
              absolute
              rounded-full
              bg-zinc-700
            "
            style={{
              left: cx,
              top: cy,

              width: 26,
              height: 26,
            }}
          />
        ))}

        {/* MONITOR */}

        <div
          className="
            absolute
            left-1/2
            top-1/2
            -translate-x-1/2
            -translate-y-1/2
            rounded-md
            bg-zinc-900
          "
          style={{
            width: 42,
            height: 24,
          }}
        />
      </div>
    </div>
  )
}