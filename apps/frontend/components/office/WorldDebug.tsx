'use client'

import {
  TILE_SIZE,
  world,
} from './world'

export default function WorldDebug() {
  return (
    <>
      {world.map((tile) => (
        <div
          key={`${tile.x}-${tile.y}`}
          className="
            absolute
            border
          "
          style={{
            left:
              tile.x *
              TILE_SIZE,

            top:
              tile.y *
              TILE_SIZE,

            width:
              TILE_SIZE,

            height:
              TILE_SIZE,

            borderColor:
              'rgba(255,255,255,0.04)',

            background:
              tile.blocked
                ? 'rgba(255,0,0,0.15)'
                : 'transparent',
          }}
        />
      ))}
    </>
  )
}