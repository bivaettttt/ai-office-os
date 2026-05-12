'use client'

import { useEffect, useState } from 'react'

type Point = {
  x: number
  y: number
}

export default function useAgentMotion(
  targetX: number,
  targetY: number
) {
  const [position, setPosition] =
    useState<Point>({
      x: targetX,
      y: targetY,
    })

  useEffect(() => {
    const interval = setInterval(() => {
      setPosition((prev) => {
        const dx =
          targetX - prev.x

        const dy =
          targetY - prev.y

        const distance =
          Math.sqrt(
            dx * dx + dy * dy
          )

        if (distance < 1) {
          return {
            x: targetX,
            y: targetY,
          }
        }

        const speed = 2.4

        return {
          x:
            prev.x +
            (dx / distance) *
              speed,

          y:
            prev.y +
            (dy / distance) *
              speed,
        }
      })
    }, 16)

    return () =>
      clearInterval(interval)
  }, [targetX, targetY])

  return position
}