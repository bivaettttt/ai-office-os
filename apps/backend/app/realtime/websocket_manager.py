import logging

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect

logger = logging.getLogger(__name__)


class WebSocketManager:

    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(
        self,
        websocket: WebSocket,
    ):

        await websocket.accept()

        self.connections.append(
            websocket
        )
        logger.info(
            "websocket connected active=%s",
            len(self.connections),
        )

    def disconnect(
        self,
        websocket: WebSocket,
    ):

        if websocket in self.connections:
            self.connections.remove(
                websocket
            )
            logger.info(
                "websocket disconnected active=%s",
                len(self.connections),
            )

    async def disconnect_all(self):
        connections = list(self.connections)

        for connection in connections:
            try:
                await connection.close()
            except Exception:
                logger.exception("websocket close failed")
            finally:
                self.disconnect(connection)

    async def broadcast(
        self,
        data,
    ):

        dead_connections = []

        for connection in self.connections:

            try:

                await connection.send_json(
                    data
                )

            except (
                WebSocketDisconnect,
                RuntimeError,
                Exception,
            ):

                logger.exception("websocket broadcast failed")

                dead_connections.append(
                    connection
                )

        for connection in dead_connections:

            self.disconnect(
                connection
            )


ws_manager = WebSocketManager()
