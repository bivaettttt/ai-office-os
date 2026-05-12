from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from app.config.settings import settings
from app.core.world import World

logger = logging.getLogger(__name__)


def persistence_path() -> Path:
    return Path(settings.PERSISTENCE_PATH)


def load_world_state(world: World) -> bool:
    if not settings.PERSISTENCE_ENABLED:
        return False

    path = persistence_path()

    if not path.exists():
        return False

    try:
        data = json.loads(
            path.read_text(encoding="utf-8")
        )
        world.hydrate(data)
        logger.info(
            "world state restored path=%s tasks=%s agents=%s",
            path,
            len(world.tasks),
            len(world.agents),
        )
        return True
    except Exception:
        logger.exception(
            "failed to restore world state path=%s",
            path,
        )
        return False


def save_world_state(world: World) -> None:
    if not settings.PERSISTENCE_ENABLED:
        return

    path = persistence_path()
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        json.dumps(
            world.serialize(),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


async def persist_world_periodically(
    world: World,
):
    while True:
        try:
            save_world_state(world)
        except Exception:
            logger.exception(
                "periodic world state save failed"
            )

        await asyncio.sleep(1)
