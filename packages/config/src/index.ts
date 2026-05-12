export type RuntimeEnvironment = "development" | "production" | "test"

export type ModelProvider = "ollama" | "local" | "mock"

export type FrontendConfig = {
  env: RuntimeEnvironment
  apiUrl: string
  wsUrl: string
}

export type BackendConfig = {
  env: RuntimeEnvironment
  host: string
  port: number
  frontendUrl: string
  modelProvider: ModelProvider
  localMode: boolean
}
