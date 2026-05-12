export const TILE_SIZE = 40

export const WORLD_WIDTH = 40
export const WORLD_HEIGHT = 20

export type TileType =
  | 'floor'
  | 'wall'
  | 'desk'

export type Tile = {
  x: number
  y: number
  type: TileType
  blocked: boolean
}

export const world: Tile[] = []

for (
  let y = 0;
  y < WORLD_HEIGHT;
  y++
) {
  for (
    let x = 0;
    x < WORLD_WIDTH;
    x++
  ) {
    world.push({
      x,
      y,

      type: 'floor',

      blocked: false,
    })
  }
}

function blockTile(
  tileX: number,
  tileY: number,
  type: TileType = 'wall'
) {
  const tile = world.find(
    (t) =>
      t.x === tileX &&
      t.y === tileY
  )

  if (!tile) return

  tile.blocked = true
  tile.type = type
}

//
// OUTER WALLS
//

for (let x = 0; x < 40; x++) {
  blockTile(x, 0)
  blockTile(x, 19)
}

for (let y = 0; y < 20; y++) {
  blockTile(0, y)
  blockTile(39, y)
}

//
// ROOM WALLS
//

for (let y = 2; y < 12; y++) {
  blockTile(13, y)
  blockTile(26, y)
}

//
// HALLWAY WALL
//

for (let x = 0; x < 40; x++) {
  if (x === 20) continue

  blockTile(x, 12)
}

//
// DOORS
//

const doors = [
  [13, 6],
  [26, 6],
  [20, 12],
]

doors.forEach(([x, y]) => {
  const tile = world.find(
    (t) =>
      t.x === x &&
      t.y === y
  )

  if (tile) {
    tile.blocked = false
    tile.type = 'floor'
  }
})