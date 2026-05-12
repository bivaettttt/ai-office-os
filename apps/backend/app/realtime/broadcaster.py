from app.realtime.websocket_manager import (
    ws_manager,
)
from app.schemas.protocol import WebSocketMessage


async def broadcast_event(
    event_type: str,
    payload: dict,
):

    await ws_manager.broadcast(
        WebSocketMessage(
            type="event.broadcast",
            payload={
                "event_type": event_type,
                "data": payload,
            },
        ).model_dump()
    )
