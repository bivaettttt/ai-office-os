'use client'

import { useEffect, useState } from 'react'

type Props = {
  name: string

  x: number
  y: number

  color: string
}

export default function Agent({
  name,
  x,
  y,
  color,
}: Props) {
  const [offset, setOffset] = useState({
    x: 0,
    y: 0,
  })

  useEffect(() => {
    const interval = setInterval(() => {
      setOffset({
        x: Math.random() * 80 - 40,
        y: Math.random() * 50 - 25,
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div
      className="
        absolute
        transition-all
        duration-[3000ms]
        ease-in-out
        flex
        flex-col
        items-center
        gap-2
        select-none
      "
      style={{
        left: x + offset.x,
        top: y + offset.y,
      }}
    >
      {/* AGENT GLOW */}

      <div
        className="
          absolute
          w-20
          h-20
          rounded-full
          blur-3xl
          opacity-30
        "
        style={{
          background: color,
        }}
      />

      {/* BODY */}

      <div
        className="
          relative
          z-10
          w-14
          h-14
          rounded-2xl
          border
          flex
          items-center
          justify-center
          text-sm
          font-black
          backdrop-blur-xl
        "
        style={{
          background: `${color}22`,
          borderColor: `${color}66`,
          color,
          boxShadow: `0 0 25px ${color}55`,
        }}
      >
        {name.slice(0, 2).toUpperCase()}
      </div>

      {/* LABEL */}

      <div
        className="
          text-xs
          font-bold
          tracking-wide
          opacity-80
        "
        style={{
          color,
        }}
      >
        {name}
      </div>
    </div>
  )
}