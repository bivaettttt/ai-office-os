import { OFFICE_RENDERER_CONFIG } from "@/engine/config/officeRendererConfig"

export type OfficeRoom = {
  id: string
  title: string
  zoneType:
    | "department"
    | "meeting"
    | "lounge"
    | "control"
  x: number
  y: number
  width: number
  height: number
  floorColor: number
  wallColor: number
  accentColor: number
}

export type Workstation = {
  id: string
  department: string
  x: number
  y: number
}

export type MeetingZone = {
  id: string
  department: string
  x: number
  y: number
  width: number
  height: number
}

export type LoungeZone = {
  id: string
  x: number
  y: number
  width: number
  height: number
}

export type ServerRack = {
  id: string
  x: number
  y: number
}

export type Plant = {
  id: string
  x: number
  y: number
}

export const officeRooms: OfficeRoom[] = [
  {
    id: "development",
    title: "Development",
    zoneType: "department",
    x: 40,
    y: 70,
    width: 520,
    height: 330,
    floorColor: 0x38465a,
    wallColor: 0x172033,
    accentColor: 0x38bdf8,
  },
  {
    id: "assistant",
    title: "Assistant",
    zoneType: "department",
    x: 860,
    y: 70,
    width: 480,
    height: 300,
    floorColor: 0x5d574e,
    wallColor: 0x302c25,
    accentColor: 0xfbbf24,
  },
  {
    id: "analytics",
    title: "Analytics",
    x: 40,
    y: 500,
    zoneType: "department",
    width: 520,
    height: 360,
    floorColor: 0x283d63,
    wallColor: 0x1d2a3a,
    accentColor: 0xa78bfa,
  },
  {
    id: "content",
    title: "Content Studio",
    zoneType: "department",
    x: 860,
    y: 650,
    width: 480,
    height: 230,
    floorColor: 0x5a4230,
    wallColor: 0x3c2918,
    accentColor: 0xfb7185,
  },
  {
    id: "meeting",
    title: "Meeting Room",
    zoneType: "meeting",
    x: 860,
    y: 410,
    width: 480,
    height: 200,
    floorColor: 0x31524d,
    wallColor: 0x173b36,
    accentColor: 0x5eead4,
  },
  {
    id: "lounge",
    title: "Lounge",
    zoneType: "lounge",
    x: 580,
    y: 720,
    width: 250,
    height: 160,
    floorColor: 0x4b3b55,
    wallColor: 0x2d2235,
    accentColor: 0xf0abfc,
  },
  {
    id: "control",
    title: "Server Control",
    zoneType: "control",
    x: 600,
    y: 70,
    width: 220,
    height: 260,
    floorColor: 0x1f3a3d,
    wallColor: 0x0f2629,
    accentColor: 0x22d3ee,
  },
]

export const departmentRooms = officeRooms.filter(
  (room) => room.zoneType === "department"
)

export const officeWorkstations: Workstation[] =
  departmentRooms.flatMap((room) => [
    {
      id: `${room.id}-desk-1`,
      department: room.id,
      x: room.x + 115,
      y: room.y + room.height - 118,
    },
    {
      id: `${room.id}-desk-2`,
      department: room.id,
      x: room.x + room.width / 2,
      y: room.y + room.height - 118,
    },
    {
      id: `${room.id}-desk-3`,
      department: room.id,
      x: room.x + room.width - 115,
      y: room.y + room.height - 118,
    },
  ])

export const meetingZones: MeetingZone[] =
  departmentRooms
    .map((room) => ({
      id: `${room.id}-focus`,
      department: room.id,
      x: room.x + room.width - 158,
      y: room.y + 78,
      width: 112,
      height: 58,
    }))
    .concat([
      {
        id: "central-meeting",
        department: "all",
        x: 970,
        y: 462,
        width: 250,
        height: 92,
      },
    ])

export const loungeZones: LoungeZone[] = [
  {
    id: "main-lounge",
    x: 625,
    y: 765,
    width: 160,
    height: 70,
  },
]

export const serverRacks: ServerRack[] = [
  {
    id: "rack-1",
    x: 640,
    y: 145,
  },
  {
    id: "rack-2",
    x: 710,
    y: 145,
  },
  {
    id: "rack-3",
    x: 780,
    y: 145,
  },
]

export const officePlants: Plant[] = [
  {
    id: "plant-dev",
    x: 75,
    y: 340,
  },
  {
    id: "plant-analytics",
    x: 520,
    y: 820,
  },
  {
    id: "plant-assistant",
    x: 1300,
    y: 330,
  },
  {
    id: "plant-lounge",
    x: 810,
    y: 850,
  },
]

export const corridor = {
  x: 575,
  y: 0,
  width: 270,
  height: OFFICE_RENDERER_CONFIG.worldHeight,
}

export const horizontalCorridor = {
  x: 40,
  y: 420,
  width: 1300,
  height: 58,
}
