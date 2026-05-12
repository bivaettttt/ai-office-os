"use client"

import { useEffect } from "react"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error("Frontend boundary error:", error)
  }, [error])

  return (
    <main className="min-h-screen bg-[#0b1018] text-white flex items-center justify-center p-6">
      <section className="w-full max-w-md border border-white/10 bg-white/5 p-6">
        <h1 className="text-xl font-semibold">
          Ошибка интерфейса
        </h1>

        <p className="mt-3 text-sm text-white/70">
          Компонент не смог отрисоваться. Можно перезапустить экран без остановки backend.
        </p>

        <button
          type="button"
          onClick={reset}
          className="mt-5 h-10 px-4 bg-cyan-500 text-black font-semibold"
        >
          Перезапустить экран
        </button>
      </section>
    </main>
  )
}
