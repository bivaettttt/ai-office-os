import type { WorldState } from "@ai-office/types"

export type ClientWebSocketMessage =
  | { type: "client.hello"; payload?: Record<string, never>; ts?: number }
  | { type: "world.subscribe"; payload?: Record<string, never>; ts?: number }
  | { type: "world.get"; payload?: Record<string, never>; ts?: number }
  | {
      type: "task.create"
      payload: {
        message?: string
        title?: string
        description?: string
        department?: string
      }
      ts?: number
    }

export type ServerWebSocketMessage =
  | {
      type: "server.hello"
      payload: { protocol: "ai-office-os.ws.v1" }
      ts: number
    }
  | {
      type: "world.snapshot" | "world.update"
      payload: WorldState
      ts: number
    }
  | {
      type: "agent.update" | "task.update"
      payload: Record<string, unknown>
      ts: number
    }
  | {
      type: "event.broadcast"
      payload: {
        event_type: string
        data: Record<string, unknown>
      }
      ts: number
    }
  | {
      type: "error"
      payload: {
        message: string
        received_type?: string
      }
      ts: number
    }

export type WebSocketMessage =
  | ClientWebSocketMessage
  | ServerWebSocketMessage
