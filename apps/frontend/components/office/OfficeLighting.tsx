export default function OfficeLighting() {
  return (
    <>
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(circle at 20% 20%, rgba(255,255,255,0.10), transparent 30%),
            radial-gradient(circle at 80% 30%, rgba(255,255,255,0.08), transparent 30%),
            radial-gradient(circle at 50% 80%, rgba(255,255,255,0.06), transparent 40%)
          `,
        }}
      />

      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'linear-gradient(to bottom, rgba(0,0,0,0.02), rgba(0,0,0,0.18))',
        }}
      />
    </>
  )
}