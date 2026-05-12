from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECTS_DIR = BASE_DIR / "generated_projects"


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Zа-яА-Я0-9]+", "_", text.lower()).strip("_")
    return slug or "project"


def create_project_structure(task: str) -> dict[str, object]:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    project_name = f"{_slugify(task)}_{timestamp}"

    root = PROJECTS_DIR / project_name

    folders = [
        root,
        root / "frontend",
        root / "frontend" / "app",
        root / "frontend" / "public",
        root / "backend",
        root / "docs",
        root / "reports",
        root / "assets",
    ]

    for folder in folders:
        folder.mkdir(parents=True, exist_ok=True)

    return {
        "project_name": project_name,
        "project_folder": str(root.resolve()),
        "frontend_folder": str((root / "frontend").resolve()),
        "backend_folder": str((root / "backend").resolve()),
        "folders": [str(folder.resolve()) for folder in folders],
    }