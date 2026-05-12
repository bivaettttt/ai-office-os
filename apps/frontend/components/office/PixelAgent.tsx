'use client'

import { useEffect, useMemo, useState } from 'react'

type Props = {
  name: string

  x: number
  y: number

  color: string
}

export default function PixelAgent({
  name,
  x,
  y,
  color,
}: Props) {
  const [position, setPosition] = useState({
    x,
    y,
  })

  const [direction, setDirection] = useState<'left' | 'right'>('right')

  useEffect(() => {
    const interval = setInterval(() => {
      const nextX = x + (Math.random() * 120 - 60)
      const nextY = y + (Math.random() * 70 - 35)

      setDirection(nextX < position.x ? 'left' : 'right')

      setPosition({
        x: nextX,
        y: nextY,
      })
    }, 3500)

    return () => clearInterval(interval)
  }, [position.x, x, y])

  const initials = useMemo(() => {
    return name.slice(0, 1).toUpperCase()
  }, [name])

  return (
    <div
      className="absolute transition-all duration-[3500ms] ease-in-out"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      {/* SHADOW */}

      <div
        className="absolute left-1/2 top-[34px] w-8 h-3 -translate-x-1/2 rounded-full blur-md opacity-40"
        style={{
          background: color,
        }}
      />

      {/* CHARACTER */}

      <div
        className={`
          relative
          w-[34px]
          h-[42px]
          transition-transform
          duration-500
          ${direction === 'left' ? '-scale-x-100' : ''}
        `}
      >
        {/* HEAD */}

        <div
          className="absolute left-[8px] top-0 w-[18px] h-[18px] rounded-md border"
          style={{
            background: color,
            borderColor: 'rgba(255,255,255,0.4)',
            boxShadow: `0 0 12px ${color}`,
          }}
        />

        {/* BODY */}

        <div
          className="absolute left-[6px] top-[16px] w-[22px] h-[16px] rounded-sm border"
          style={{
            background: 'rgba(15,23,42,0.95)',
            borderColor: `${color}88`,
          }}
        />

        {/* LEGS */}

        <div
          className="absolute left-[9px] top-[30px] w-[5px] h-[10px] rounded-sm"
          style={{
            background: color,
          }}
        />

        <div
          className="absolute left-[20px] top-[30px] w-[5px] h-[10px] rounded-sm"
          style={{
            background: color,
          }}
        />

        {/* FACE */}

        <div className="absolute top-[3px] left-[11px] text-[8px] font-black text-black">
          {initials}
        </div>
      </div>

      {/* NAME */}

      <div
        className="absolute top-[48px] left-1/2 -translate-x-1/2 whitespace-nowrap text-[10px] font-bold tracking-wider"
        style={{
          color,
        }}
      >
        {name}
      </div>
    </div>
  )
}
