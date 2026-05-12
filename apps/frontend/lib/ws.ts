"use client"

import { frontendConfig } from "@/lib/config"
import type {
  ClientWebSocketMessage,
  ServerWebSocketMessage,
} from "@ai-office/protocol"

type Listener = (message: ServerWebSocketMessage) => void

class RealtimeClient {
  private socket: WebSocket | null = null
  private listeners: Listener[] = []
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private reconnectAttempts = 0
  private manuallyClosed = false

  connect() {
    if (
      this.socket &&
      (this.socket.readyState === WebSocket.OPEN ||
        this.socket.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    this.manuallyClosed = false
    this.socket = new WebSocket(frontendConfig.wsUrl)

    this.socket.onopen = () => {
      this.reconnectAttempts = 0
      this.send({ type: "client.hello" })
      this.send({ type: "world.subscribe" })
    }

    this.socket.onmessage = (event) => {
      try {
        const data = JSON.parse(
          event.data
        ) as ServerWebSocketMessage

        this.listeners.forEach((listener) =>
          listener(data)
        )
      } catch (err) {
        console.error("WS parse error:", err)
      }
    }

    this.socket.onerror = (event) => {
      console.error("WS error:", event)
    }

    this.socket.onclose = () => {
      this.socket = null

      if (!this.manuallyClosed) {
        this.scheduleReconnect()
      }
    }
  }

  close() {
    this.manuallyClosed = true

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }

    this.socket?.close()
    this.socket = null
  }

  send(message: ClientWebSocketMessage) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          ...message,
          ts: Date.now() / 1000,
        })
      )
    }
  }

  subscribe(listener: Listener) {
    this.listeners.push(listener)

    return () => {
      this.listeners = this.listeners.filter(
        (item) => item !== listener
      )
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return

    const delay = Math.min(
      1000 * 2 ** this.reconnectAttempts,
      10000
    )

    this.reconnectAttempts += 1
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, delay)
  }
}

export const realtimeClient = new RealtimeClient()
