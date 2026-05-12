import { OFFICE_RENDERER_CONFIG } from "@/engine/config/officeRendererConfig"
import {
  corridor,
  departmentRooms,
  horizontalCorridor,
  loungeZones,
  meetingZones,
  officeWorkstations,
  serverRacks,
} from "@/engine/world/officeMap"

export type GridPoint = {
  col: number
  row: number
}

export type WorldPoint = {
  x: number
  y: number
}

export class NavigationGrid {
  readonly tileSize = OFFICE_RENDERER_CONFIG.tileSize
  readonly cols = Math.ceil(
    OFFICE_RENDERER_CONFIG.worldWidth / this.tileSize
  )
  readonly rows = Math.ceil(
    OFFICE_RENDERER_CONFIG.worldHeight / this.tileSize
  )

  private readonly walkable: boolean[][]

  constructor() {
    this.walkable = Array.from(
      {
        length: this.rows,
      },
      () => Array(this.cols).fill(false)
    )

    this.markWalkableRect(corridor)
    this.markWalkableRect(horizontalCorridor)

    for (const room of departmentRooms) {
      this.markWalkableRect({
        x: room.x + this.tileSize,
        y: room.y + this.tileSize,
        width: room.width - this.tileSize * 2,
        height: room.height - this.tileSize * 2,
      })
      this.markDoorToCorridor(room)
    }

    for (const zone of meetingZones) {
      this.markWalkableRect(zone)
    }

    for (const zone of loungeZones) {
      this.markWalkableRect(zone)
    }

    for (const desk of officeWorkstations) {
      this.markBlockedCircle(desk, 20)
    }

    for (const rack of serverRacks) {
      this.markBlockedCircle(rack, 24)
    }
  }

  isWalkable(point: GridPoint) {
    return (
      point.col >= 0 &&
      point.row >= 0 &&
      point.col < this.cols &&
      point.row < this.rows &&
      this.walkable[point.row][point.col]
    )
  }

  worldToGrid(point: WorldPoint): GridPoint {
    return {
      col: Math.floor(point.x / this.tileSize),
      row: Math.floor(point.y / this.tileSize),
    }
  }

  gridToWorld(point: GridPoint): WorldPoint {
    return {
      x: point.col * this.tileSize + this.tileSize / 2,
      y: point.row * this.tileSize + this.tileSize / 2,
    }
  }

  nearestWalkable(point: WorldPoint): GridPoint {
    const start = this.worldToGrid(point)

    if (this.isWalkable(start)) {
      return start
    }

    for (let radius = 1; radius < 8; radius += 1) {
      for (
        let row = start.row - radius;
        row <= start.row + radius;
        row += 1
      ) {
        for (
          let col = start.col - radius;
          col <= start.col + radius;
          col += 1
        ) {
          const candidate = {
            col,
            row,
          }

          if (this.isWalkable(candidate)) {
            return candidate
          }
        }
      }
    }

    return start
  }

  randomPointInDepartment(
    department: string,
    reserved: Set<string>
  ): WorldPoint | null {
    const room = departmentRooms.find(
      (item) => item.id === department
    )

    if (!room) {
      return null
    }

    for (let attempt = 0; attempt < 20; attempt += 1) {
      const x =
        room.x +
        this.tileSize +
        Math.random() *
          (room.width - this.tileSize * 2)
      const y =
        room.y +
        this.tileSize +
        Math.random() *
          (room.height - this.tileSize * 2)

      const grid = this.nearestWalkable({
        x,
        y,
      })
      const key = this.key(grid)

      if (!reserved.has(key)) {
        reserved.add(key)
        return this.gridToWorld(grid)
      }
    }

    return null
  }

  departmentInterestPoint(
    department: string,
    reserved: Set<string>
  ): WorldPoint | null {
    const candidates = [
      ...officeWorkstations.filter(
        (desk) => desk.department === department
      ),
      ...meetingZones.filter(
        (zone) => zone.department === department
      ),
    ]

    if (candidates.length === 0) {
      return this.randomPointInDepartment(
        department,
        reserved
      )
    }

    const target =
      candidates[
        Math.floor(Math.random() * candidates.length)
      ]
    const grid = this.nearestWalkable({
      x: target.x,
      y: target.y + this.tileSize,
    })
    const key = this.key(grid)

    if (reserved.has(key)) {
      return this.randomPointInDepartment(
        department,
        reserved
      )
    }

    reserved.add(key)
    return this.gridToWorld(grid)
  }

  randomLoungePoint(
    reserved: Set<string>
  ): WorldPoint | null {
    const zone =
      loungeZones[
        Math.floor(Math.random() * loungeZones.length)
      ]

    if (!zone) {
      return null
    }

    const grid = this.nearestWalkable({
      x: zone.x + Math.random() * zone.width,
      y: zone.y + Math.random() * zone.height,
    })
    const key = this.key(grid)

    if (reserved.has(key)) {
      return null
    }

    reserved.add(key)
    return this.gridToWorld(grid)
  }

  meetingPoint(
    index: number,
    reserved: Set<string>
  ): WorldPoint | null {
    const zone = meetingZones.find(
      (item) => item.department === "all"
    )

    if (!zone) {
      return null
    }

    const offsets = [
      {
        x: -55,
        y: 0,
      },
      {
        x: 0,
        y: -18,
      },
      {
        x: 55,
        y: 0,
      },
    ]
    const offset =
      offsets[index % offsets.length]
    const grid = this.nearestWalkable({
      x: zone.x + zone.width / 2 + offset.x,
      y: zone.y + zone.height / 2 + offset.y,
    })
    const key = this.key(grid)

    if (reserved.has(key)) {
      return null
    }

    reserved.add(key)
    return this.gridToWorld(grid)
  }

  key(point: GridPoint) {
    return `${point.col}:${point.row}`
  }

  private markWalkableRect(rect: {
    x: number
    y: number
    width: number
    height: number
  }) {
    const start = this.worldToGrid({
      x: rect.x,
      y: rect.y,
    })
    const end = this.worldToGrid({
      x: rect.x + rect.width,
      y: rect.y + rect.height,
    })

    for (let row = start.row; row <= end.row; row += 1) {
      for (
        let col = start.col;
        col <= end.col;
        col += 1
      ) {
        if (
          row >= 0 &&
          col >= 0 &&
          row < this.rows &&
          col < this.cols
        ) {
          this.walkable[row][col] = true
        }
      }
    }
  }

  private markBlockedCircle(
    point: WorldPoint,
    radius: number
  ) {
    const center = this.worldToGrid(point)
    const range = Math.ceil(radius / this.tileSize)

    for (
      let row = center.row - range;
      row <= center.row + range;
      row += 1
    ) {
      for (
        let col = center.col - range;
        col <= center.col + range;
        col += 1
      ) {
        if (
          row >= 0 &&
          col >= 0 &&
          row < this.rows &&
          col < this.cols
        ) {
          this.walkable[row][col] = false
        }
      }
    }
  }

  private markDoorToCorridor(room: {
    x: number
    y: number
    width: number
    height: number
  }) {
    const doorY = room.y + room.height / 2 - 30

    if (room.x < corridor.x) {
      this.markWalkableRect({
        x: room.x + room.width - this.tileSize,
        y: doorY,
        width: corridor.x - (room.x + room.width) + 90,
        height: 80,
      })
    } else {
      this.markWalkableRect({
        x: corridor.x + corridor.width - 10,
        y: doorY,
        width:
          room.x -
          (corridor.x + corridor.width) +
          90,
        height: 80,
      })
    }
  }
}
