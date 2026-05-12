import {
  Container,
  FederatedPointerEvent,
} from "pixi.js"
import { OFFICE_RENDERER_CONFIG } from "@/engine/config/officeRendererConfig"

type CameraControllerOptions = {
  camera: Container
  canvas: HTMLCanvasElement
  width: () => number
  height: () => number
}

export class CameraController {
  private readonly camera: Container
  private readonly canvas: HTMLCanvasElement
  private readonly width: () => number
  private readonly height: () => number
  private baseScale = 1
  private zoom = 1
  private targetX = 0
  private targetY = 0
  private targetZoom = 1
  private dragging = false
  private lastPointer = {
    x: 0,
    y: 0,
  }

  constructor(options: CameraControllerOptions) {
    this.camera = options.camera
    this.canvas = options.canvas
    this.width = options.width
    this.height = options.height

    this.canvas.addEventListener(
      "wheel",
      this.handleWheel,
      {
        passive: false,
      }
    )
    this.canvas.addEventListener(
      "pointerdown",
      this.handlePointerDown
    )
    window.addEventListener(
      "pointermove",
      this.handlePointerMove
    )
    window.addEventListener(
      "pointerup",
      this.handlePointerUp
    )
  }

  resize() {
    this.baseScale = Math.min(
      this.width() /
        OFFICE_RENDERER_CONFIG.worldWidth,
      this.height() /
        OFFICE_RENDERER_CONFIG.worldHeight
    )

    this.zoom = Math.min(
      Math.max(
        this.zoom,
        OFFICE_RENDERER_CONFIG.minZoom
      ),
      OFFICE_RENDERER_CONFIG.maxZoom
    )
    this.targetZoom = this.zoom
    this.center()
  }

  center() {
    const scale = this.baseScale * this.zoom

    this.targetX =
      (this.width() -
        OFFICE_RENDERER_CONFIG.worldWidth * scale) /
      2
    this.targetY =
      (this.height() -
        OFFICE_RENDERER_CONFIG.worldHeight * scale) /
      2
    this.applyImmediate()
  }

  tick() {
    this.zoom +=
      (this.targetZoom - this.zoom) *
      OFFICE_RENDERER_CONFIG.cameraEase

    const scale = this.baseScale * this.zoom
    this.camera.scale.set(scale)

    this.camera.x +=
      (this.targetX - this.camera.x) *
      OFFICE_RENDERER_CONFIG.cameraEase
    this.camera.y +=
      (this.targetY - this.camera.y) *
      OFFICE_RENDERER_CONFIG.cameraEase
  }

  destroy() {
    this.canvas.removeEventListener(
      "wheel",
      this.handleWheel
    )
    this.canvas.removeEventListener(
      "pointerdown",
      this.handlePointerDown
    )
    window.removeEventListener(
      "pointermove",
      this.handlePointerMove
    )
    window.removeEventListener(
      "pointerup",
      this.handlePointerUp
    )
  }

  private applyImmediate() {
    this.camera.x = this.targetX
    this.camera.y = this.targetY
    this.camera.scale.set(this.baseScale * this.zoom)
  }

  private handleWheel = (event: WheelEvent) => {
    event.preventDefault()

    const beforeScale = this.baseScale * this.zoom
    const worldX =
      (event.offsetX - this.targetX) / beforeScale
    const worldY =
      (event.offsetY - this.targetY) / beforeScale

    const delta =
      event.deltaY > 0 ? 0.9 : 1.1
    this.targetZoom = Math.min(
      OFFICE_RENDERER_CONFIG.maxZoom,
      Math.max(
        OFFICE_RENDERER_CONFIG.minZoom,
        this.targetZoom * delta
      )
    )

    const afterScale =
      this.baseScale * this.targetZoom
    this.targetX = event.offsetX - worldX * afterScale
    this.targetY = event.offsetY - worldY * afterScale
  }

  private handlePointerDown = (
    event: PointerEvent | FederatedPointerEvent
  ) => {
    this.dragging = true
    this.lastPointer = {
      x: event.clientX,
      y: event.clientY,
    }
  }

  private handlePointerMove = (
    event: PointerEvent
  ) => {
    if (!this.dragging) {
      return
    }

    const dx = event.clientX - this.lastPointer.x
    const dy = event.clientY - this.lastPointer.y
    this.lastPointer = {
      x: event.clientX,
      y: event.clientY,
    }

    this.targetX += dx
    this.targetY += dy
  }

  private handlePointerUp = () => {
    this.dragging = false
  }
}
