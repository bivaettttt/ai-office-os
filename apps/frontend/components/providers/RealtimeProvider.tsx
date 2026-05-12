"use client"

import { useEffect } from "react"
import { useWorldStore } from "@/store/useWorldStore"

export default function RealtimeProvider() {
  const connectWebSocket = useWorldStore(
    (state) => state.connectWebSocket
  )

  useEffect(() => {
    connectWebSocket()
  }, [connectWebSocket])

  return null
}
