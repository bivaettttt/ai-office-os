import { frontendConfig } from "@/lib/config"


export async function getWorld() {
  const response = await fetch(`${frontendConfig.apiUrl}/world`)

  return response.json()
}


export async function createTask(data: {
  title: string
  description: string
  department: string
}) {
  const response = await fetch(`${frontendConfig.apiUrl}/world/task`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  })

  return response.json()
}
