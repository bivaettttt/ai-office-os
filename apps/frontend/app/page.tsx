'use client'

import CommandCenter from '@/components/office/CommandCenter'
import OfficeRendererCanvas from '@/components/office/OfficeRendererCanvas'

import {
  useWorldStore,
  eventToText,
} from '@/store/useWorldStore'
import type { Agent } from '@/store/useWorldStore'

export default function Home() {

  const agentsMap =
    useWorldStore(
      (state) => state.agents
    )

  const events =
    useWorldStore(
      (state) => state.events
    )

  const agents: Agent[] =
    Object.values(
      agentsMap || {}
    )

  return (

    <main className="w-screen h-screen overflow-hidden bg-[#0b1018] text-white flex flex-col">

      <style jsx global>{`
        .pixelated {
          image-rendering: pixelated;
        }
      `}</style>

      {/* TOPBAR */}

      <header className="h-[58px] border-b border-white/10 bg-[#0d1420] flex items-center justify-between px-5 shrink-0">

        <div className="flex items-center gap-4">

          <div className="text-xl">
            ☰
          </div>

          <div className="text-[18px] font-bold tracking-[0.15em]">
            AI Office OS
          </div>

        </div>

        <div className="flex items-center gap-10 text-sm">

          <div className="flex items-center gap-2 text-green-400">

            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />

            Realtime simulation active

          </div>

        </div>

      </header>

      {/* BODY */}

      <section className="flex-1 flex overflow-hidden">

        {/* LEFT */}

        <aside className="w-[260px] border-r border-white/10 bg-[#111827] p-3 flex flex-col gap-3 overflow-auto">

          <div className="rounded-2xl bg-white/5 border border-white/10 p-4">

            <div className="text-2xl mb-4">
              Управление
            </div>

            <CommandCenter />

          </div>

          <div className="rounded-2xl bg-white/5 border border-white/10 p-4">

            <div className="text-2xl mb-4">
              AI Events
            </div>

            <div className="space-y-2 max-h-[500px] overflow-auto">

              {events
                .slice()
                .reverse()
                .map((event, index) => (

                  <div
                    key={index}
                    className="text-sm text-white/70 border-b border-white/5 pb-2"
                  >
                    {eventToText(event)}
                  </div>

                ))}

            </div>

          </div>

        </aside>

        {/* CENTER */}

        <div className="flex-1 overflow-hidden bg-[#0f1722]">

          <OfficeRendererCanvas />

        </div>

        {/* RIGHT */}

        <aside className="w-[260px] border-l border-white/10 bg-[#111827] p-3 flex flex-col gap-3 overflow-auto">

          <div className="rounded-2xl bg-white/5 border border-white/10 p-5">

            <div className="text-3xl mb-4">
              Статистика
            </div>

            <div className="space-y-4">

              <div>

                <div className="text-white/60 mb-1">
                  Агентов онлайн
                </div>

                <div className="text-4xl font-bold text-cyan-400">

                  {agents.length}

                </div>

              </div>

              <div>

                <div className="text-white/60 mb-1">
                  Working
                </div>

                <div className="text-4xl font-bold text-green-400">

                  {
                    agents.filter(
                      (a) =>
                        a.status ===
                        'working'
                    ).length
                  }

                </div>

              </div>

              <div>

                <div className="text-white/60 mb-1">
                  Errors
                </div>

                <div className="text-4xl font-bold text-red-400">

                  {
                    agents.filter(
                      (a) =>
                        a.status ===
                        'error'
                    ).length
                  }

                </div>

              </div>

            </div>

          </div>

        </aside>

      </section>

    </main>
  )
}
