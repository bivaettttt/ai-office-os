type Props = {
  x: number
  y: number
}

export default function Plant({
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
      {/* POT */}

      <div
        className="
          absolute
          left-[8px]
          top-[18px]
          w-[18px]
          h-[18px]
          rounded-sm
          bg-[#7c5a3a]
        "
      />

      {/* LEAVES */}

      <div
        className="
          absolute
          left-0
          top-0
          w-[34px]
          h-[34px]
          rounded-full
          bg-[#3f7c47]
        "
      />

      <div
        className="
          absolute
          left-[8px]
          top-[-6px]
          w-[22px]
          h-[22px]
          rounded-full
          bg-[#5c9b63]
        "
      />
    </div>
  )
}