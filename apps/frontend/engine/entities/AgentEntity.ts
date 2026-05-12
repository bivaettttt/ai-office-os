import {
  Circle,
  Container,
  Graphics,
  Text,
} from "pixi.js"
import type { Agent } from "@ai-office/types"
import { OFFICE_RENDERER_CONFIG } from "@/engine/config/officeRendererConfig"
import type { WorldPoint } from "@/engine/world/navigationGrid"

const STATUS_COLORS: Record<string, number> = {
  idle: 0x22c55e,
  walking: 0x38bdf8,
  working: 0xfacc15,
  error: 0xef4444,
  offline: 0x64748b,
}

const DEPARTMENT_COLORS: Record<string, number> = {
  development: 0x38bdf8,
  analytics: 0xa78bfa,
  assistant: 0xfbbf24,
  content: 0xfb7185,
}

export type VisualActivity =
  | "idle"
  | "walking"
  | "working"
  | "meeting"
  | "lounge"
  | "thinking"

function statusColor(status: string) {
  return STATUS_COLORS[status] ?? STATUS_COLORS.idle
}

export class AgentEntity {
  readonly id: string
  readonly view = new Container()

  private readonly body = new Graphics()
  private readonly shadow = new Graphics()
  private readonly ring = new Graphics()
  private readonly thinkingIndicator = new Graphics()
  private readonly progressRing = new Graphics()
  private readonly activityBubble = new Graphics()
  private readonly activityIcon = new Text({
    text: "",
    style: {
      fill: 0x0f1722,
      fontFamily: "Arial",
      fontSize: 10,
      fontWeight: "700",
      align: "center",
    },
  })
  private readonly taskText = new Text({
    text: "",
    style: {
      fill: 0xe2e8f0,
      fontFamily: "Arial",
      fontSize: 9,
      align: "center",
    },
  })
  private readonly nameText = new Text({
    text: "",
    style: {
      fill: 0xffffff,
      fontFamily: "Arial",
      fontSize: 12,
      fontWeight: "700",
      align: "center",
    },
  })
  private readonly metaText = new Text({
    text: "",
    style: {
      fill: 0xcbd5e1,
      fontFamily: "Arial",
      fontSize: 10,
      align: "center",
    },
  })

  private agent: Agent
  private path: WorldPoint[] = []
  private status = "idle"
  private movementState: VisualActivity = "idle"
  private visualActivity: VisualActivity = "idle"
  private taskDestinationId: string | null = null
  private phase = 0
  private selected = false
  private hovered = false
  private roamCooldown =
    1 + Math.random() * 3
  private direction = {
    x: 0,
    y: 1,
  }

  constructor(
    agent: Agent,
    onSelect: (agent: Agent) => void
  ) {
    this.id = agent.id
    this.agent = agent

    this.view.eventMode = "static"
    this.view.cursor = "pointer"
    this.view.hitArea = new Circle(
      0,
      0,
      30
    )
    this.view.on("pointertap", () => {
      onSelect(this.agent)
    })
    this.view.on("pointerover", () => {
      this.hovered = true
      this.redrawBody()
    })
    this.view.on("pointerout", () => {
      this.hovered = false
      this.redrawBody()
    })

    this.view.addChild(
      this.shadow,
      this.ring,
      this.body,
      this.progressRing,
      this.thinkingIndicator,
      this.activityBubble,
      this.activityIcon,
      this.nameText,
      this.metaText,
      this.taskText
    )

    this.shadow
      .ellipse(0, 18, 22, 7)
      .fill({
        color: 0x000000,
        alpha: 0.28,
      })

    this.nameText.anchor.set(0.5)
    this.metaText.anchor.set(0.5)
    this.nameText.y = -38
    this.metaText.y = -23
    this.thinkingIndicator.y = -8
    this.thinkingIndicator.x = 20
    this.activityBubble.y = -51
    this.activityIcon.anchor.set(0.5)
    this.activityIcon.y = -51
    this.taskText.anchor.set(0.5)
    this.taskText.y = 28

    this.view.x = agent.position_x
    this.view.y = agent.position_y

    this.update(agent)
  }

  update(agent: Agent) {
    this.agent = agent
    this.status = agent.status
    this.nameText.text = agent.name
    this.metaText.text = `${agent.department} · ${this.movementState}`
    this.redrawBody()
  }

  setPath(path: WorldPoint[]) {
    this.path = path.slice(1)

    if (this.path.length > 0) {
      this.movementState = "walking"
    }
  }

  setTaskPath(
    taskId: string,
    path: WorldPoint[]
  ) {
    if (this.taskDestinationId === taskId) {
      return
    }

    this.taskDestinationId = taskId
    this.setPath(path)
    this.setVisualActivity("working")
  }

  setVisualActivity(activity: VisualActivity) {
    this.visualActivity = activity
    this.redrawBody()
  }

  hasPath() {
    return this.path.length > 0
  }

  getAgent() {
    return this.agent
  }

  getPosition(): WorldPoint {
    return {
      x: this.view.x,
      y: this.view.y,
    }
  }

  getCurrentTileKey() {
    return `${Math.floor(
      this.view.x / OFFICE_RENDERER_CONFIG.tileSize
    )}:${Math.floor(
      this.view.y / OFFICE_RENDERER_CONFIG.tileSize
    )}`
  }

  getRoamCooldown() {
    return this.roamCooldown
  }

  resetRoamCooldown() {
    this.roamCooldown =
      2.5 + Math.random() * 4
  }

  holdFor(seconds: number) {
    this.path = []
    this.roamCooldown = seconds
  }

  setSelected(selected: boolean) {
    this.selected = selected
    this.redrawBody()
  }

  tick(deltaSeconds: number) {
    this.phase += deltaSeconds
    this.roamCooldown -= deltaSeconds

    const moving = this.advanceAlongPath(deltaSeconds)

    if (
      this.status === "working" ||
      this.agent.current_task_id ||
      this.visualActivity === "working"
    ) {
      this.movementState = "working"
    } else if (moving) {
      this.movementState = "walking"
    } else if (
      this.visualActivity === "meeting" ||
      this.visualActivity === "lounge"
    ) {
      this.movementState = this.visualActivity
    } else {
      this.movementState = "idle"
    }

    this.metaText.text = `${this.agent.department} · ${this.movementState}`
    this.applyAnimation()

    return moving
  }

  destroy() {
    this.view.destroy({
      children: true,
    })
  }

  private advanceAlongPath(deltaSeconds: number) {
    const target = this.path[0]

    if (!target) {
      return false
    }

    const dx = target.x - this.view.x
    const dy = target.y - this.view.y
    const distance = Math.hypot(dx, dy)
    const step =
      OFFICE_RENDERER_CONFIG.agentSpeed *
      deltaSeconds

    if (distance <= step) {
      this.view.x = target.x
      this.view.y = target.y
      this.path.shift()

      if (this.path.length === 0) {
        this.resetRoamCooldown()
      }

      return true
    }

    this.direction = {
      x: dx / distance,
      y: dy / distance,
    }
    this.view.x += this.direction.x * step
    this.view.y += this.direction.y * step

    return true
  }

  private redrawBody() {
    this.ring.clear()
    this.body.clear()
    this.progressRing.clear()
    this.activityBubble.clear()

    if (this.selected || this.hovered) {
      this.ring
        .circle(0, 0, this.selected ? 27 : 23)
        .stroke({
          color: this.selected ? 0x22d3ee : 0xffffff,
          width: this.selected ? 3 : 2,
          alpha: this.selected ? 0.95 : 0.55,
        })
    }

    this.body
      .circle(0, 0, 18)
      .fill(
        DEPARTMENT_COLORS[
          this.agent.department
        ] ?? statusColor(this.status)
      )
      .stroke({
        color: 0xffffff,
        width: 2,
        alpha: 0.75,
      })

    this.body
      .rect(-5, -22, 10, 8)
      .fill(statusColor(this.status))

    if (
      this.status === "working" ||
      this.agent.task_progress > 0
    ) {
      const progress =
        Math.max(8, this.agent.task_progress) / 100
      this.progressRing
        .arc(
          0,
          0,
          24,
          -Math.PI / 2,
          -Math.PI / 2 + Math.PI * 2 * progress
        )
        .stroke({
          color: 0x22d3ee,
          width: 3,
          alpha: 0.9,
        })
    }

    this.thinkingIndicator.clear()
    this.thinkingIndicator
      .circle(0, 0, 4)
      .fill({
        color: 0xffffff,
        alpha: 0.75,
      })
      .circle(8, -5, 3)
      .fill({
        color: 0xffffff,
        alpha: 0.55,
      })

    this.activityBubble
      .roundRect(-14, -62, 28, 20, 8)
      .fill({
        color: 0xffffff,
        alpha: 0.85,
      })
      .stroke({
        color: 0x0f1722,
        width: 1,
        alpha: 0.35,
      })

    this.activityIcon.text =
      this.status === "working"
        ? "T"
        : this.visualActivity === "meeting"
          ? "M"
          : this.visualActivity === "lounge"
            ? "R"
            : "..."

    const hasTask =
      Boolean(this.agent.current_task_id) ||
      this.status === "working"

    this.taskText.text = hasTask
      ? `task ${this.agent.task_progress}%`
      : ""
  }

  private applyAnimation() {
    this.thinkingIndicator.visible =
      this.movementState === "idle" ||
      this.movementState === "thinking"
    this.activityBubble.visible =
      this.movementState === "working" ||
      this.movementState === "meeting" ||
      this.movementState === "lounge"
    this.activityIcon.visible =
      this.activityBubble.visible
    this.taskText.visible =
      this.status === "working" ||
      this.agent.task_progress > 0

    if (this.movementState === "working") {
      const pulse =
        1 + Math.sin(this.phase * 6) * 0.06
      this.body.scale.set(pulse)
      this.body.y = 0
      return
    }

    if (this.movementState === "meeting") {
      this.body.y = Math.sin(this.phase * 4) * 1
      this.body.scale.set(1.04)
      return
    }

    if (this.movementState === "lounge") {
      this.body.y = Math.sin(this.phase * 1.5) * 2
      this.body.scale.set(0.96)
      return
    }

    if (this.movementState === "walking") {
      const bob = Math.sin(this.phase * 10) * 3
      this.body.y = bob
      this.body.scale.set(
        this.direction.x < -0.05 ? -1 : 1,
        1
      )
      return
    }

    this.body.y = Math.sin(this.phase * 2) * 1.5
    this.body.scale.set(1)
  }
}
