from pydantic import BaseModel


class DebugRequest(BaseModel):
    traceback: str
    project_folder: str | None = None