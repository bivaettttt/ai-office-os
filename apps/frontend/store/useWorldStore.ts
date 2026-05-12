"use client"

import { create } from "zustand"
import type {
  Agent,
  Event,
  WorldState as SharedWorldState,
} from "@ai-office/types"
import { realtimeClient } from "@/lib/ws"
import type { ServerWebSocketMessage } from "@ai-office/protocol"

type WorldStore = SharedWorldState & {
  socketConnected: boolean
  setWorld: (world: SharedWorldState) => void
  setAgents: (agents: Record<string, Agent>) => void
  addEvent: (event: string | Event | Record<string, unknown>) => void
  connectWebSocket: () => void
}

export type WorldStoreState = Pick<
  WorldStore,
  | "agents"
  | "departments"
  | "tasks"
  | "events"
  | "socketConnected"
>

function eventToText(
  event: string | Event | Record<string, unknown>
) {
  if (typeof event === "string") {
    return event
  }

  if ("type" in event && typeof event.type === "string") {
    return event.type
  }

  return JSON.stringify(event)
}

export function applyWorldMessageToState(
  state: WorldStoreState,
  message: ServerWebSocketMessage
): WorldStoreState {
  if (
    message.type === "world.snapshot" ||
    message.type === "world.update"
  ) {
    return {
      ...message.payload,
      socketConnected: true,
    }
  }

  if (message.type === "event.broadcast") {
    return {
      ...state,
      events: [
        ...state.events,
        {
          type: message.payload.event_type,
          payload: message.payload.data,
          ts: message.ts,
        },
      ],
    }
  }

  return state
}

function applyMessage(
  message: ServerWebSocketMessage,
  set: (
    partial:
      | Partial<WorldStore>
      | ((state: WorldStore) => Partial<WorldStore>)
  ) => void
) {
  set((state) =>
    applyWorldMessageToState(
      state,
      message
    )
  )
}

let subscribed = false

export const useWorldStore = create<WorldStore>((set) => ({
  agents: {},
  departments: {},
  tasks: {},
  events: [],
  socketConnected: false,

  setWorld: (world) =>
    set({
      ...world,
      socketConnected: true,
    }),

  setAgents: (agents) =>
    set({
      agents,
    }),

  addEvent: (event) =>
    set((state) => ({
      events: [...state.events, event],
    })),

  connectWebSocket: () => {
    if (!subscribed) {
      subscribed = true

      realtimeClient.subscribe((message) => {
        applyMessage(message, set)
      })
    }

    realtimeClient.connect()
  },
}))

export type { Agent }
export { eventToText }
