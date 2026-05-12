import type {
  GridPoint,
  NavigationGrid,
  WorldPoint,
} from "@/engine/world/navigationGrid"

type NodeRecord = GridPoint & {
  f: number
  g: number
  parent?: string
}

function heuristic(
  a: GridPoint,
  b: GridPoint
) {
  return (
    Math.abs(a.col - b.col) +
    Math.abs(a.row - b.row)
  )
}

function neighbors(point: GridPoint): GridPoint[] {
  return [
    {
      col: point.col + 1,
      row: point.row,
    },
    {
      col: point.col - 1,
      row: point.row,
    },
    {
      col: point.col,
      row: point.row + 1,
    },
    {
      col: point.col,
      row: point.row - 1,
    },
  ]
}

export function findPath(
  grid: NavigationGrid,
  from: WorldPoint,
  to: WorldPoint
): WorldPoint[] {
  const start = grid.nearestWalkable(from)
  const goal = grid.nearestWalkable(to)
  const startKey = grid.key(start)
  const goalKey = grid.key(goal)

  if (startKey === goalKey) {
    return [grid.gridToWorld(goal)]
  }

  const open = new Map<string, NodeRecord>()
  const closed = new Set<string>()
  const records = new Map<string, NodeRecord>()

  const startRecord = {
    ...start,
    f: heuristic(start, goal),
    g: 0,
  }

  open.set(startKey, startRecord)
  records.set(startKey, startRecord)

  while (open.size > 0) {
    let currentKey = ""
    let current: NodeRecord | null = null

    for (const [key, candidate] of open) {
      if (!current || candidate.f < current.f) {
        current = candidate
        currentKey = key
      }
    }

    if (!current) {
      break
    }

    if (currentKey === goalKey) {
      return reconstructPath(
        grid,
        records,
        currentKey
      )
    }

    open.delete(currentKey)
    closed.add(currentKey)

    for (const next of neighbors(current)) {
      if (!grid.isWalkable(next)) {
        continue
      }

      const nextKey = grid.key(next)

      if (closed.has(nextKey)) {
        continue
      }

      const nextG = current.g + 1
      const existing = records.get(nextKey)

      if (!existing || nextG < existing.g) {
        const record = {
          ...next,
          g: nextG,
          f: nextG + heuristic(next, goal),
          parent: currentKey,
        }

        records.set(nextKey, record)
        open.set(nextKey, record)
      }
    }
  }

  return []
}

function reconstructPath(
  grid: NavigationGrid,
  records: Map<string, NodeRecord>,
  endKey: string
) {
  const points: WorldPoint[] = []
  let key: string | undefined = endKey

  while (key) {
    const record = records.get(key)

    if (!record) {
      break
    }

    points.unshift(grid.gridToWorld(record))
    key = record.parent
  }

  return points
}
