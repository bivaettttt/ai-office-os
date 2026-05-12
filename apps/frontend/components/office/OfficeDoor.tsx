type Props = {
  x: number
  y: number
}

export default function OfficeDoor({
  x,
  y,
}: Props) {
  return (
    <div
      className="
        absolute
        rounded-full
      "
      style={{
        left: x,
        top: y,

        width: 22,
        height: 22,

        background:
          'rgba(34,211,238,0.9)',

        boxShadow: `
          0 0 20px rgba(34,211,238,0.8)
        `,
      }}
    />
  )
}