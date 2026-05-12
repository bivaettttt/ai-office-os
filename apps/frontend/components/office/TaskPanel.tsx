'use client'

import { useState } from 'react'

import { frontendConfig } from '@/lib/config'


type TaskResponse = {
  status: string
  department: string
  task_id: string
}


export default function TaskPanel() {

  const [title, setTitle] = useState('')

  const [department, setDepartment] =
    useState('development')

  const [priority, setPriority] =
    useState('normal')

  const [loading, setLoading] = useState(false)

  const [result, setResult] =
    useState<TaskResponse | null>(null)


  async function createTask() {

    if (!title.trim()) {
      return
    }

    try {

      setLoading(true)

      const response = await fetch(
        `${frontendConfig.apiUrl}/tasks`,
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            title,
            description: title,
            department,
            priority,
          }),
        }
      )

      const data = await response.json()

      setResult(data)

      setTitle('')

    } catch (error) {

      console.error(error)

    } finally {

      setLoading(false)
    }
  }


  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-5">

      <div className="text-3xl mb-4">
        Task command
      </div>

      <input
        value={title}
        onChange={(e) =>
          setTitle(e.target.value)
        }
        placeholder="Task title"
        className="w-full h-12 rounded-xl bg-[#111827] border border-white/10 px-4 text-white outline-none"
      />

      <select
        value={department}
        onChange={(e) =>
          setDepartment(e.target.value)
        }
        className="mt-3 w-full h-11 rounded-xl bg-[#111827] border border-white/10 px-4 text-white outline-none"
      >
        <option value="development">
          Development
        </option>
        <option value="analytics">
          Analytics
        </option>
        <option value="assistant">
          Assistant
        </option>
        <option value="content">
          Content
        </option>
      </select>

      <select
        value={priority}
        onChange={(e) =>
          setPriority(e.target.value)
        }
        className="mt-3 w-full h-11 rounded-xl bg-[#111827] border border-white/10 px-4 text-white outline-none"
      >
        <option value="low">Low</option>
        <option value="normal">Normal</option>
        <option value="high">High</option>
      </select>

      <button
        onClick={createTask}
        disabled={loading}
        className="mt-4 w-full h-12 rounded-xl bg-cyan-500 hover:bg-cyan-400 transition font-bold text-black"
      >
        {
          loading
            ? 'Queueing task...'
            : 'Create task'
        }
      </button>

      {result && (

        <div className="mt-4 rounded-xl bg-green-500/10 border border-green-500/20 p-4 text-sm">

          <div>
            Status: {result.status}
          </div>

          <div>
            Department: {result.department}
          </div>

          <div className="break-all">
            Task ID: {result.task_id}
          </div>
        </div>
      )}
    </div>
  )
}
