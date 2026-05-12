# AI Office OS WebSocket Protocol

Protocol version: `ai-office-os.ws.v1`

Endpoint: `ws://<backend-host>/ws`

Client to server:

- `client.hello`: initial handshake.
- `world.subscribe`: request continuous world sync.
- `world.get`: request an immediate world snapshot.
- `task.create`: reserved for websocket task creation. HTTP `/tasks` remains the current stable write path.

Server to client:

- `server.hello`: confirms protocol version.
- `world.snapshot`: full world state after subscribe/get.
- `world.update`: periodic full world state sync.
- `event.broadcast`: normalized event bus broadcast.
- `agent.update`: reserved for targeted agent patches.
- `task.update`: reserved for targeted task patches.
- `error`: protocol or server error message.

`world.update` is intentionally a full snapshot in this foundation phase. Delta patches can be added later after persistence and replay semantics are defined.
