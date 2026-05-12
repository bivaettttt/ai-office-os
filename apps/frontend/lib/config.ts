import type { FrontendConfig } from "@ai-office/config"

export const frontendConfig: FrontendConfig = {
  env:
    (process.env.NEXT_PUBLIC_ENV as FrontendConfig["env"]) ||
    "development",
  apiUrl:
    process.env.NEXT_PUBLIC_API_URL ||
    "http://127.0.0.1:8000",
  wsUrl:
    process.env.NEXT_PUBLIC_WS_URL ||
    "ws://127.0.0.1:8000/ws",
}
