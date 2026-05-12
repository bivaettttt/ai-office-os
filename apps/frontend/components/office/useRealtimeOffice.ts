"use client"

import { useEffect, useState } from "react"

import {
  realtimeClient,
} from "@/lib/ws"

import {
  officeStore,
} from "./liveOfficeStore"


export function useRealtimeOffice() {

  const [, forceUpdate] =
    useState(0)

  useEffect(() => {

    realtimeClient.connect()

    const unsubscribe =
      realtimeClient.subscribe(
        (message) => {

          // =========================
          // AGENT STATUS
          // =========================

          if (
            message.type === "event.broadcast" &&
            message.payload.event_type === "agent.status"
          ) {

            const payload = message.payload.data as {
              agent?: string
              status?: string
              task?: string
              phase?: string
            }

            if (!payload.agent) {
              return
            }

            officeStore.agents[payload.agent] = {
              name: payload.agent,
              status:
                payload.status || "idle",
              task:
                payload.task || "",
              phase:
                payload.phase || "",
            }

            forceUpdate(
              (x) => x + 1
            )
          }
        }
      )

    return () => {
      unsubscribe()
    }

  }, [])

  return {
    agents:
      officeStore.agents,
  }
}
