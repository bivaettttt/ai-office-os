import asyncio
import logging

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from app.config.settings import settings
from app.core.world import world
from app.realtime.websocket_manager import (
    ws_manager,
)
from app.schemas.protocol import WebSocketMessage

router = APIRouter()
logger = logging.getLogger(__name__)


async def send_world_updates(
    websocket: WebSocket,
):
    while True:
        await websocket.send_json(
            WebSocketMessage(
                type="world.update",
                payload=world.serialize(),
            ).model_dump()
        )
        await asyncio.sleep(
            settings.WORLD_SYNC_INTERVAL_SECONDS
        )


async def receive_client_messages(
    websocket: WebSocket,
):
    while True:
        raw_message = await websocket.receive_json()
        message_type = raw_message.get("type")

        if message_type in {
            "client.hello",
            "world.subscribe",
            "world.get",
        }:
            await websocket.send_json(
                WebSocketMessage(
                    type="world.snapshot",
                    payload=world.serialize(),
                ).model_dump()
            )
        else:
            await websocket.send_json(
                WebSocketMessage(
                    type="error",
                    payload={
                        "message": "Unsupported websocket message",
                        "received_type": message_type,
                    },
                ).model_dump()
            )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):

    await ws_manager.connect(websocket)

    sender_task = None
    receiver_task = None

    try:
        await websocket.send_json(
            WebSocketMessage(
                type="server.hello",
                payload={
                    "protocol": "ai-office-os.ws.v1",
                },
            ).model_dump()
        )

        sender_task = asyncio.create_task(
            send_world_updates(websocket)
        )
        receiver_task = asyncio.create_task(
            receive_client_messages(websocket)
        )

        done, pending = await asyncio.wait(
            {sender_task, receiver_task},
            return_when=asyncio.FIRST_EXCEPTION,
        )

        for task in done:
            task.result()

        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

    except asyncio.CancelledError:
        ws_manager.disconnect(websocket)
        raise

    except Exception:
        logger.exception("websocket endpoint failed")
        ws_manager.disconnect(websocket)

    finally:
        for task in [sender_task, receiver_task]:
            if task and not task.done():
                task.cancel()
