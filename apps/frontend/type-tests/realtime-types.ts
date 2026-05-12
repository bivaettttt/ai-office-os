import type {
  ServerWebSocketMessage,
} from "@ai-office/protocol"
import {
  applyWorldMessageToState,
  type WorldStoreState,
} from "@/store/useWorldStore"

const initialState: WorldStoreState = {
  agents: {},
  departments: {},
  tasks: {},
  events: [],
  socketConnected: false,
}

const snapshot = {
  type: "world.snapshot",
  payload: {
    agents: {},
    departments: {},
    tasks: {},
    events: [],
  },
  ts: 1,
} satisfies ServerWebSocketMessage

const update = {
  type: "world.update",
  payload: {
    agents: {},
    departments: {},
    tasks: {},
    events: [],
  },
  ts: 2,
} satisfies ServerWebSocketMessage

const afterSnapshot =
  applyWorldMessageToState(
    initialState,
    snapshot
  )

const afterUpdate =
  applyWorldMessageToState(
    afterSnapshot,
    update
  )

if (!afterUpdate.socketConnected) {
  throw new Error("expected connected state")
}
