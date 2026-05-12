import {
  Application,
  type Ticker,
} from "pixi.js"
import type { WorldState } from "@ai-office/types"
import {
  OfficeScene,
  type ActivityFeedItem,
  type SelectedAgentInfo,
} from "@/engine/scenes/OfficeScene"
import { OFFICE_RENDERER_CONFIG } from "@/engine/config/officeRendererConfig"
import { CameraController } from "@/engine/renderer/CameraController"

export type RendererStats = {
  fps: number
  agentCount: number
  worldTick: number
  movingAgents: number
  selectedEntityId: string | null
  currentActivity: string
  renderMs: number
  activeTasks: number
  simulationSpeed: number
  paused: boolean
}

type RendererOptions = {
  host: HTMLElement
  onStats?: (stats: RendererStats) => void
  onSelectAgent?: (
    agent: SelectedAgentInfo | null
  ) => void
  onActivity?: (item: ActivityFeedItem) => void
}

export class OfficeRendererEngine {
  private readonly host: HTMLElement
  private readonly onStats?: (stats: RendererStats) => void
  private readonly onSelectAgent?: (
    agent: SelectedAgentInfo | null
  ) => void
  private readonly onActivity?: (
    item: ActivityFeedItem
  ) => void
  private app: Application | null = null
  private scene: OfficeScene | null = null
  private cameraController: CameraController | null = null
  private pointerDown = {
    x: 0,
    y: 0,
  }
  private resizeObserver: ResizeObserver | null = null
  private worldTick = 0
  private activeTasks = 0
  private simulationSpeed = 1
  private paused = false
  private destroyed = false
  private lastStatsAt = 0

  constructor(options: RendererOptions) {
    this.host = options.host
    this.onStats = options.onStats
    this.onSelectAgent = options.onSelectAgent
    this.onActivity = options.onActivity
  }

  async init(initialWorld: WorldState) {
    if (this.destroyed) {
      return
    }

    const app = new Application()

    await app.init({
      background: OFFICE_RENDERER_CONFIG.backgroundColor,
      antialias: true,
      autoDensity: true,
      resolution: Math.min(
        window.devicePixelRatio || 1,
        2
      ),
      resizeTo: this.host,
    })

    app.canvas.style.width = "100%"
    app.canvas.style.height = "100%"
    app.canvas.style.display = "block"
    app.stage.eventMode = "static"

    this.host.appendChild(app.canvas)

    const scene = new OfficeScene(
      this.onSelectAgent,
      this.onActivity
    )
    app.stage.addChild(scene.camera)

    const cameraController = new CameraController({
      camera: scene.camera,
      canvas: app.canvas,
      width: () => this.host.clientWidth,
      height: () => this.host.clientHeight,
    })
    cameraController.resize()
    scene.syncWorld(initialWorld)

    app.ticker.add(this.tick)

    this.resizeObserver = new ResizeObserver(() => {
      cameraController.resize()
    })
    this.resizeObserver.observe(this.host)
    app.canvas.addEventListener(
      "pointerdown",
      this.handlePointerDown
    )
    app.canvas.addEventListener(
      "click",
      this.handleCanvasClick
    )

    this.app = app
    this.scene = scene
    this.cameraController = cameraController
  }

  syncWorld(world: WorldState) {
    this.worldTick += 1
    this.activeTasks = Object.values(
      world.tasks
    ).filter(
      (task) =>
        task.status !== "completed" &&
        task.status !== "failed"
    ).length
    this.scene?.syncWorld(world)
  }

  setPaused(paused: boolean) {
    this.paused = paused
  }

  setSimulationSpeed(speed: number) {
    this.simulationSpeed = Math.min(
      3,
      Math.max(0.25, speed)
    )
  }

  destroy() {
    this.destroyed = true
    this.resizeObserver?.disconnect()
    this.resizeObserver = null
    this.cameraController?.destroy()
    this.cameraController = null

    if (this.app) {
      this.app.ticker.remove(this.tick)
      this.app.canvas.removeEventListener(
        "pointerdown",
        this.handlePointerDown
      )
      this.app.canvas.removeEventListener(
        "click",
        this.handleCanvasClick
      )
    }

    if (this.scene && this.app) {
      this.app.stage.removeChild(this.scene.camera)
    }

    this.scene?.destroy()
    this.scene = null

    this.app?.destroy(true)
    this.app = null
  }

  private tick = (ticker: Ticker) => {
    const startedAt = performance.now()
    const deltaSeconds =
      ticker.deltaMS / 1000

    this.cameraController?.tick()

    if (!this.paused) {
      this.scene?.tick(
        deltaSeconds * this.simulationSpeed
      )
    }
    const renderMs = performance.now() - startedAt

    if (
      performance.now() - this.lastStatsAt <
      250
    ) {
      return
    }

    this.lastStatsAt = performance.now()

    this.onStats?.({
      fps: Math.round(ticker.FPS),
      agentCount:
        this.scene?.getAgentCount() ?? 0,
      worldTick: this.worldTick,
      movingAgents:
        this.scene?.getMovingCount() ?? 0,
      selectedEntityId:
        this.scene?.getSelectedAgentId() ?? null,
      currentActivity:
        this.scene?.getCurrentActivity() ?? "idle",
      renderMs:
        Math.round(renderMs * 10) / 10,
      activeTasks: this.activeTasks,
      simulationSpeed: this.simulationSpeed,
      paused: this.paused,
    })
  }

  private handlePointerDown = (
    event: PointerEvent
  ) => {
    this.pointerDown = {
      x: event.clientX,
      y: event.clientY,
    }
  }

  private handleCanvasClick = (
    event: MouseEvent
  ) => {
    if (!this.scene) {
      return
    }

    const dragDistance = Math.hypot(
      event.clientX - this.pointerDown.x,
      event.clientY - this.pointerDown.y
    )

    if (dragDistance > 5) {
      return
    }

    const scale =
      this.scene.camera.scale.x || 1
    this.scene.selectAt({
      x: (event.offsetX - this.scene.camera.x) / scale,
      y: (event.offsetY - this.scene.camera.y) / scale,
    })
  }
}
