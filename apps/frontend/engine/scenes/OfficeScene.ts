import {
  Container,
  Graphics,
  Text,
} from "pixi.js"
import type {
  Agent,
  WorldState,
} from "@ai-office/types"
import { AgentEntity } from "@/engine/entities/AgentEntity"
import {
  corridor,
  horizontalCorridor,
  loungeZones,
  meetingZones,
  officePlants,
  officeRooms,
  officeWorkstations,
  serverRacks,
} from "@/engine/world/officeMap"
import { OFFICE_RENDERER_CONFIG } from "@/engine/config/officeRendererConfig"
import { NavigationGrid } from "@/engine/world/navigationGrid"
import { findPath } from "@/engine/world/pathfinding"
import type { WorldPoint } from "@/engine/world/navigationGrid"

export type SelectedAgentInfo = {
  id: string
  name: string
  role: string
  department: string
  status: string
  currentTaskId?: string | null
  capabilities?: string[]
  isManager?: boolean
  managerForDepartment?: string | null
  x: number
  y: number
}

export type ActivityFeedItem = {
  id: string
  ts: number
  message: string
}

export class OfficeScene {
  readonly camera = new Container()
  readonly world = new Container()
  readonly navigation = new NavigationGrid()

  private readonly gridLayer = new Graphics()
  private readonly mapLayer = new Container()
  private readonly ambienceLayer = new Graphics()
  private readonly entityLayer = new Container()
  private readonly agents = new Map<string, AgentEntity>()
  private selectedAgentId: string | null = null
  private movingCount = 0
  private currentActivity = "idle"
  private elapsed = 0
  private socialMeetingIn = 7 + Math.random() * 7

  constructor(
    private readonly onSelectAgent?: (
      agent: SelectedAgentInfo | null
    ) => void,
    private readonly onActivity?: (
      item: ActivityFeedItem
    ) => void
  ) {
    this.camera.addChild(this.world)
    this.world.addChild(
      this.gridLayer,
      this.mapLayer,
      this.ambienceLayer,
      this.entityLayer
    )

    this.drawGrid()
    this.drawOfficeMap()
  }

  syncWorld(worldState: WorldState) {
    const incomingAgents = Object.values(
      worldState.agents
    )
    const activeIds = new Set<string>()

    for (const agent of incomingAgents) {
      activeIds.add(agent.id)
      this.syncAgent(agent, worldState)
    }

    for (const [id, entity] of this.agents) {
      if (!activeIds.has(id)) {
        this.entityLayer.removeChild(entity.view)
        entity.destroy()
        this.agents.delete(id)
      }
    }
  }

  tick(deltaSeconds: number) {
    let moving = 0
    this.elapsed += deltaSeconds

    this.updateAmbience()
    this.scheduleSocialMeeting(deltaSeconds)
    this.assignRoamingPaths()

    for (const agent of this.agents.values()) {
      if (agent.tick(deltaSeconds)) {
        moving += 1
      }
    }

    this.movingCount = moving
    this.currentActivity =
      moving > 0 ? "roaming" : "steady"

    if (this.selectedAgentId) {
      const selected = this.agents.get(
        this.selectedAgentId
      )

      if (selected) {
        this.onSelectAgent?.(
          this.toSelectedInfo(selected)
        )
      }
    }
  }

  getAgentCount() {
    return this.agents.size
  }

  getMovingCount() {
    return this.movingCount
  }

  getCurrentActivity() {
    return this.currentActivity
  }

  getSelectedAgentId() {
    return this.selectedAgentId
  }

  selectAt(point: WorldPoint) {
    let nearest: AgentEntity | null = null
    let nearestDistance = Number.POSITIVE_INFINITY

    for (const entity of this.agents.values()) {
      const position = entity.getPosition()
      const distance = Math.hypot(
        position.x - point.x,
        position.y - point.y
      )

      if (distance <= nearestDistance) {
        nearest = entity
        nearestDistance = distance
      }
    }

    if (nearest) {
      this.selectAgent(nearest.getAgent())
    }
  }

  destroy() {
    for (const agent of this.agents.values()) {
      agent.destroy()
    }

    this.agents.clear()
    this.camera.destroy({
      children: true,
    })
  }

  private syncAgent(
    agent: Agent,
    worldState: WorldState
  ) {
    let entity = this.agents.get(agent.id)

    if (!entity) {
      const spawn = this.navigation.gridToWorld(
        this.navigation.nearestWalkable({
          x: agent.position_x,
          y: agent.position_y,
        })
      )

      entity = new AgentEntity(
        {
          ...agent,
          position_x: spawn.x,
          position_y: spawn.y,
        },
        this.selectAgent
      )
      this.agents.set(agent.id, entity)
      this.entityLayer.addChild(entity.view)
    }

    entity.update(agent)

    if (agent.current_task_id) {
      const task =
        worldState.tasks[agent.current_task_id]

      if (
        task &&
        task.status !== "completed" &&
        task.status !== "failed"
      ) {
        const target =
          this.taskDeskForAgent(agent)
        const path = findPath(
          this.navigation,
          entity.getPosition(),
          target
        )

        if (path.length > 1) {
          entity.setTaskPath(task.id, path)
        } else {
          entity.setVisualActivity("working")
        }
      }
    }
  }

  private selectAgent = (agent: Agent) => {
    this.selectedAgentId = agent.id

    for (const entity of this.agents.values()) {
      entity.setSelected(entity.id === agent.id)
    }

    const selected = this.agents.get(agent.id)
    this.onSelectAgent?.(
      selected ? this.toSelectedInfo(selected) : null
    )
  }

  private toSelectedInfo(
    entity: AgentEntity
  ): SelectedAgentInfo {
    const agent = entity.getAgent()
    const position = entity.getPosition()

    return {
      id: agent.id,
      name: agent.name,
      role: agent.role,
      department: agent.department,
      status: agent.status,
      currentTaskId: agent.current_task_id,
      capabilities: agent.capabilities || [],
      isManager: agent.is_manager || false,
      managerForDepartment: (
        agent.manager_for_department || null
      ),
      x: Math.round(position.x),
      y: Math.round(position.y),
    }
  }

  private assignRoamingPaths() {
    const reserved = new Set<string>()

    for (const agent of this.agents.values()) {
      reserved.add(agent.getCurrentTileKey())
    }

    for (const agent of this.agents.values()) {
      if (
        agent.hasPath() ||
        agent.getRoamCooldown() > 0
      ) {
        continue
      }

      const source = agent.getPosition()
      const domainAgent = agent.getAgent()

      if (
        domainAgent.current_task_id ||
        domainAgent.status === "working"
      ) {
        agent.setVisualActivity("working")
        continue
      }

      const activityRoll = Math.random()
      let target: WorldPoint | null = null

      if (activityRoll < 0.28) {
        target =
          this.navigation.departmentInterestPoint(
            domainAgent.department,
            reserved
          )
        agent.setVisualActivity("working")
        this.emitActivity(
          `${domainAgent.role} started focused work`
        )
      } else if (activityRoll < 0.45) {
        target =
          this.navigation.randomLoungePoint(
            reserved
          )
        agent.setVisualActivity("lounge")
        this.emitActivity(
          `${domainAgent.name} moved to lounge`
        )
      } else {
        target =
          this.navigation.randomPointInDepartment(
            domainAgent.department,
            reserved
          )
        agent.setVisualActivity("thinking")
      }

      if (!target) {
        agent.resetRoamCooldown()
        continue
      }

      const path = findPath(
        this.navigation,
        source,
        target
      )

      if (path.length > 1) {
        agent.setPath(path)
      } else {
        agent.resetRoamCooldown()
      }
    }
  }

  private scheduleSocialMeeting(
    deltaSeconds: number
  ) {
    this.socialMeetingIn -= deltaSeconds

    if (this.socialMeetingIn > 0) {
      return
    }

    this.socialMeetingIn =
      14 + Math.random() * 12

    const candidates = Array.from(
      this.agents.values()
    )
      .filter((agent) => !agent.hasPath())
      .filter(
        (agent) =>
          !agent.getAgent().current_task_id
      )
      .sort(() => Math.random() - 0.5)
      .slice(0, 3)

    if (candidates.length < 2) {
      return
    }

    const reserved = new Set<string>()

    candidates.forEach((agent, index) => {
      const target = this.navigation.meetingPoint(
        index,
        reserved
      )

      if (!target) {
        return
      }

      const path = findPath(
        this.navigation,
        agent.getPosition(),
        target
      )

      if (path.length > 1) {
        agent.setVisualActivity("meeting")
        agent.setPath(path)
      }
    })

    this.emitActivity(
      `${candidates.length} agents entered meeting room`
    )
  }

  private emitActivity(message: string) {
    this.onActivity?.({
      id: `${Date.now()}-${Math.random()}`,
      ts: Date.now(),
      message,
    })
  }

  private taskDeskForAgent(agent: Agent): WorldPoint {
    const desks = officeWorkstations.filter(
      (desk) => desk.department === agent.department
    )

    if (desks.length === 0) {
      return {
        x: agent.position_x,
        y: agent.position_y,
      }
    }

    const index = Array.from(agent.id).reduce(
      (sum, char) => sum + char.charCodeAt(0),
      0
    )
    const desk = desks[index % desks.length]

    return {
      x: desk.x,
      y: desk.y + 52,
    }
  }

  private updateAmbience() {
    const phase =
      (Math.sin(this.elapsed * 0.25) + 1) / 2

    this.ambienceLayer.clear()
    this.ambienceLayer
      .rect(
        0,
        0,
        OFFICE_RENDERER_CONFIG.worldWidth,
        OFFICE_RENDERER_CONFIG.worldHeight
      )
      .fill({
        color: 0x0ea5e9,
        alpha: 0.025 + phase * 0.025,
      })
  }

  private drawGrid() {
    const tile = OFFICE_RENDERER_CONFIG.tileSize

    this.gridLayer.clear()

    for (
      let x = 0;
      x <= OFFICE_RENDERER_CONFIG.worldWidth;
      x += tile
    ) {
      this.gridLayer
        .moveTo(x, 0)
        .lineTo(
          x,
          OFFICE_RENDERER_CONFIG.worldHeight
        )
    }

    for (
      let y = 0;
      y <= OFFICE_RENDERER_CONFIG.worldHeight;
      y += tile
    ) {
      this.gridLayer
        .moveTo(0, y)
        .lineTo(
          OFFICE_RENDERER_CONFIG.worldWidth,
          y
        )
    }

    this.gridLayer.stroke({
      color: OFFICE_RENDERER_CONFIG.gridColor,
      width: 1,
      alpha: 0.18,
    })
  }

  private drawOfficeMap() {
    const base = new Graphics()
    base
      .rect(
        0,
        0,
        OFFICE_RENDERER_CONFIG.worldWidth,
        OFFICE_RENDERER_CONFIG.worldHeight
      )
      .fill(OFFICE_RENDERER_CONFIG.backgroundColor)

    const corridorGraphic = new Graphics()
    corridorGraphic
      .rect(
        corridor.x,
        corridor.y,
        corridor.width,
        corridor.height
      )
      .fill(OFFICE_RENDERER_CONFIG.corridorColor)
      .stroke({
        color: OFFICE_RENDERER_CONFIG.wallColor,
        width: 4,
      })

    const horizontalCorridorGraphic = new Graphics()
    horizontalCorridorGraphic
      .rect(
        horizontalCorridor.x,
        horizontalCorridor.y,
        horizontalCorridor.width,
        horizontalCorridor.height
      )
      .fill({
        color: OFFICE_RENDERER_CONFIG.corridorColor,
        alpha: 0.82,
      })
      .stroke({
        color: OFFICE_RENDERER_CONFIG.wallColor,
        width: 3,
        alpha: 0.8,
      })

    this.mapLayer.addChild(
      base,
      corridorGraphic,
      horizontalCorridorGraphic
    )

    for (const room of officeRooms) {
      const roomGraphic = new Graphics()
      roomGraphic
        .rect(room.x, room.y, room.width, room.height)
        .fill(room.floorColor)
        .stroke({
          color: room.wallColor,
          width: 8,
        })

      const accent = new Graphics()
      accent
        .rect(room.x + 14, room.y + 48, room.width - 28, 4)
        .fill({
          color: room.accentColor,
          alpha: 0.65,
        })

      const title = new Text({
        text: room.title,
        style: {
          fill: 0xffffff,
          fontFamily: "Arial",
          fontSize: 20,
          fontWeight: "700",
        },
      })
      title.x = room.x + 18
      title.y = room.y + 16

      this.mapLayer.addChild(roomGraphic, accent, title)
    }

    for (const zone of meetingZones) {
      const meeting = new Graphics()
      meeting
        .roundRect(
          zone.x,
          zone.y,
          zone.width,
          zone.height,
          10
        )
        .fill({
          color: 0x0f766e,
          alpha: 0.35,
        })
        .stroke({
          color: 0x5eead4,
          width: 2,
          alpha: 0.5,
        })

      const label = new Text({
        text: "Meeting",
        style: {
          fill: 0xa7f3d0,
          fontFamily: "Arial",
          fontSize: 11,
          fontWeight: "700",
        },
      })
      label.x = zone.x + 12
      label.y = zone.y + 20

      this.mapLayer.addChild(meeting, label)
    }

    for (const desk of officeWorkstations) {
      const workstation = this.drawDesk(
        desk.x,
        desk.y
      )

      this.mapLayer.addChild(workstation)
    }

    for (const zone of loungeZones) {
      const sofa = new Graphics()
      sofa
        .roundRect(zone.x, zone.y, zone.width, 30, 10)
        .fill(0x7e5bef)
        .roundRect(zone.x + 14, zone.y + 36, 60, 34, 10)
        .fill(0x6d28d9)
        .roundRect(zone.x + 88, zone.y + 36, 60, 34, 10)
        .fill(0x6d28d9)

      this.mapLayer.addChild(sofa)
    }

    for (const rack of serverRacks) {
      const server = new Graphics()
      server
        .roundRect(rack.x - 22, rack.y - 52, 44, 104, 5)
        .fill(0x111827)
        .stroke({
          color: 0x22d3ee,
          width: 2,
          alpha: 0.45,
        })

      for (let i = 0; i < 5; i += 1) {
        server
          .rect(rack.x - 14, rack.y - 38 + i * 18, 28, 4)
          .fill(i % 2 === 0 ? 0x22c55e : 0x38bdf8)
      }

      this.mapLayer.addChild(server)
    }

    for (const plant of officePlants) {
      const graphic = new Graphics()
      graphic
        .rect(plant.x - 8, plant.y + 8, 16, 16)
        .fill(0x854d0e)
        .circle(plant.x - 8, plant.y, 13)
        .fill(0x16a34a)
        .circle(plant.x + 8, plant.y - 3, 13)
        .fill(0x22c55e)

      this.mapLayer.addChild(graphic)
    }
  }

  private drawDesk(x: number, y: number) {
    const workstation = new Graphics()

    workstation
        .roundRect(x - 42, y - 24, 84, 48, 4)
        .fill({
          color: OFFICE_RENDERER_CONFIG.workstationColor,
          alpha: 0.42,
        })
        .stroke({
          color: 0x93c5fd,
          width: 2,
          alpha: 0.5,
        })
        .rect(x - 24, y - 38, 48, 18)
        .fill(0x0f172a)
        .rect(x - 18, y - 34, 36, 10)
        .fill(0x38bdf8)
        .rect(x - 4, y - 20, 8, 10)
        .fill(0x64748b)

    return workstation
  }
}
