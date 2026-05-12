from collections import defaultdict
from typing import Callable
import asyncio
import logging

from app.realtime.broadcaster import (
    broadcast_event,
)

logger = logging.getLogger(__name__)


class EventBus:

    def __init__(self):

        self.listeners = defaultdict(list)

    def subscribe(
        self,
        event_name: str,
        callback: Callable,
    ):

        self.listeners[event_name].append(
            callback
        )

    async def emit(
        self,
        event_name: str,
        data=None,
    ):

        payload = data or {}

        try:
            from app.core.world import world

            world.add_event(
                event_name,
                payload,
            )
        except Exception:
            logger.exception(
                "failed to append world event"
            )

        # =====================================
        # BROADCAST TO FRONTEND
        # =====================================

        await broadcast_event(
            event_name,
            payload,
        )

        # =====================================
        # INTERNAL LISTENERS
        # =====================================

        listeners = self.listeners.get(
            event_name,
            []
        )

        tasks = []

        for listener in listeners:
            tasks.append(listener(payload))

        if tasks:
            await asyncio.gather(*tasks)


event_bus = EventBus()
