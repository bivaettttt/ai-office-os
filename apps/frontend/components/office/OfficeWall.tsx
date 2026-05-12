type Props = {
  x: number
  y: number
  width: number
  height: number
}

export default function OfficeWall({
  x,
  y,
  width,
  height,
}: Props) {
  return (
    <div
      className="absolute"
      style={{
        left: x,
        top: y,

        width,
        height,

        background: `
          linear-gradient(
            180deg,
            #8d949b,
            #6b7280
          )
        `,

        border:
          '1px solid rgba(0,0,0,0.25)',

        boxShadow: `
          inset 0 2px 4px rgba(255,255,255,0.15),
          inset 0 -2px 4px rgba(0,0,0,0.2),
          0 4px 10px rgba(0,0,0,0.2)
        `,
      }}
    >
      {/* GLASS LINE */}

      <div
        className="absolute inset-0 opacity-20"
        style={{
          background: `
            repeating-linear-gradient(
              90deg,
              rgba(255,255,255,0.4) 0px,
              rgba(255,255,255,0.4) 2px,
              transparent 2px,
              transparent 18px
            )
          `,
        }}
      />
    </div>
  )
}