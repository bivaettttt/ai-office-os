export default function PixelFloor() {
  return (
    <>
      {/* WOOD FLOOR */}

      <div
        className="absolute inset-0"
        style={{
          background: `
            linear-gradient(
              90deg,
              #d7c3a5 0px,
              #d7c3a5 78px,
              #cfb594 78px,
              #cfb594 80px
            )
          `,
          backgroundSize: '80px 80px',
        }}
      />

      {/* FLOOR SHADOW */}

      <div
        className="absolute inset-0 opacity-[0.08]"
        style={{
          background: `
            linear-gradient(
              to bottom,
              rgba(0,0,0,0),
              rgba(0,0,0,0.4)
            )
          `,
        }}
      />

      {/* TILE GRID */}

      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: `
            linear-gradient(
              to right,
              black 1px,
              transparent 1px
            ),
            linear-gradient(
              to bottom,
              black 1px,
              transparent 1px
            )
          `,
          backgroundSize: '40px 40px',
        }}
      />
    </>
  )
}