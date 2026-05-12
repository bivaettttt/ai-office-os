type Props = {
  x: number
  y: number
  color: string
}

export default function Workstation({
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
      {/* shadow */}

      <div
        className="absolute top-[42px] left-[8px] w-[90px] h-[26px] rounded-full blur-xl opacity-20"
        style={{
          background: '#000',
        }}
      />

      {/* desk */}

      <div
        className="relative w-[92px] h-[54px] rounded-[16px]"
        style={{
          background:
            'linear-gradient(to bottom, #8b6b4a, #6f5338)',

          boxShadow: `
            inset 0 2px 0 rgba(255,255,255,0.25),
            0 8px 20px rgba(0,0,0,0.2)
          `,
        }}
      >
        {/* monitor */}

        <div
          className="absolute left-[20px] top-[8px] w-[50px] h-[22px] rounded-[6px]"
          style={{
            background:
              'linear-gradient(to bottom, #2d3748, #111827)',

            boxShadow:
              '0 2px 8px rgba(0,0,0,0.35)',
          }}
        />

        {/* keyboard */}

        <div
          className="absolute left-[22px] top-[36px] w-[46px] h-[6px] rounded-full"
          style={{
            background: '#d6d3d1',
          }}
        />
      </div>
    </div>
  )
}