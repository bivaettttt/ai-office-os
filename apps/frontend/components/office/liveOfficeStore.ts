export type LiveAgentState = {
  name: string
  status: string
  task: string
  phase: string
}

type Store = {
  agents: Record<
    string,
    LiveAgentState
  >
}

export const officeStore: Store = {
  agents: {},
}