import asyncio
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.runtime import router as runtime_router
from app.api.world import router as world_router
from app.api.ws import router as ws_router
from app.api.tasks import router as tasks_router
from app.api.commands import router as commands_router
from app.api.tools import router as tools_router
from app.api.approvals import router as approvals_router
from app.api.llm import router as llm_router

from app.agents.manager_agent import ManagerAgent
from app.agents.debug_agent import fix_traceback
from app.agents.terminal_agent import run_terminal_command

from app.core.bootstrap import bootstrap_world
from app.core.world import world

from app.core.orchestration.task_orchestrator import (
    task_orchestrator,
)

from app.memory.agent_memory import (
    agent_memory,
)

from app.schemas.chat import ChatRequest
from app.schemas.debug import DebugRequest
from app.schemas.terminal import TerminalRequest

from app.simulation import simulate_agents

from app.listeners.memory_listener import (
    register_memory_listeners,
)
from app.config.logging import configure_logging
from app.config.settings import settings
from app.core.persistence import (
    load_world_state,
    persist_world_periodically,
    save_world_state,
)
from app.realtime.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):

    configure_logging()

    logger.info(
        "AI Office OS starting env=%s model_provider=%s local_mode=%s",
        settings.ENV,
        settings.MODEL_PROVIDER,
        settings.LOCAL_MODE,
    )

    # =====================================================
    # VISUAL SIMULATION
    # =====================================================

    simulation_task = asyncio.create_task(
        simulate_agents(world),
        name="office-simulation",
    )

    # =====================================================
    # TASK ORCHESTRATION
    # =====================================================

    orchestration_task = asyncio.create_task(
        task_orchestrator.process_tasks(),
        name="task-orchestrator",
    )

    persistence_task = asyncio.create_task(
        persist_world_periodically(world),
        name="world-persistence",
    )

    try:
        yield
    finally:
        logger.info("AI Office OS shutting down")

        for task in [
            simulation_task,
            orchestration_task,
            persistence_task,
        ]:
            task.cancel()

        await asyncio.gather(
            simulation_task,
            orchestration_task,
            persistence_task,
            return_exceptions=True,
        )

        save_world_state(world)

        await ws_manager.disconnect_all()

# =========================================================
# APP
# =========================================================

app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# =========================================================
# CORS
# =========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=settings.cors_origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)

# =========================================================
# ROUTERS
# =========================================================

app.include_router(runtime_router)
app.include_router(world_router)
app.include_router(ws_router)
app.include_router(tasks_router)
app.include_router(commands_router)
app.include_router(tools_router)
app.include_router(approvals_router)
app.include_router(llm_router)

# =========================================================
# BOOTSTRAP
# =========================================================

manager = ManagerAgent()

bootstrap_world()

load_world_state(world)

register_memory_listeners()

# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "status": "AI Office OS online",
    }

# =========================================================
# AGENTS
# =========================================================

@app.get("/agents")
def get_agents():

    return manager.get_agents()

# =========================================================
# MEMORY
# =========================================================

@app.get("/memory")
def get_memory():

    return agent_memory

# =========================================================
# CHAT
# =========================================================

@app.post("/chat")
async def chat(req: ChatRequest):

    return await manager.process(
        req.message
    )

# =========================================================
# DEBUG
# =========================================================

@app.post("/debug")
def debug(req: DebugRequest):

    project_folder = req.project_folder

    if not project_folder:

        last = agent_memory.get(
            "last_saved_project",
            {},
        )

        project_folder = last.get(
            "folder"
        )

    return fix_traceback(

        traceback_text=req.traceback,

        project_folder=project_folder,
    )

# =========================================================
# TERMINAL
# =========================================================

@app.post("/terminal")
def terminal(req: TerminalRequest):

    cwd = req.cwd

    last = agent_memory.get(
        "last_saved_project",
        {},
    )

    if not cwd:

        command = req.command.strip().lower()

        # =====================================================
        # FRONTEND COMMANDS
        # =====================================================

        if (

            command.startswith("npm ")

            or command.startswith("npx ")

        ):

            cwd = (

                last.get("frontend_folder")

                or last.get("folder")
            )

        # =====================================================
        # BACKEND COMMANDS
        # =====================================================

        elif (

            command.startswith("python")

            or command.startswith("uvicorn")

        ):

            cwd = (

                last.get("backend_folder")

                or last.get("folder")
            )

        # =====================================================
        # DEFAULT
        # =====================================================

        else:

            cwd = last.get("folder")

    return run_terminal_command(

        command=req.command,

        cwd=cwd,
    )
