from __future__ import annotations

import os
import signal
import socket
import subprocess
import threading
import time

from pathlib import Path
from typing import Optional


# =========================================================
# RUNTIME MANAGER
# =========================================================

class RuntimeManager:

    def __init__(self):

        self.process: Optional[subprocess.Popen] = None

        self.pid: Optional[int] = None

        self.port: Optional[int] = None

        self.cwd: Optional[str] = None

        self.command: Optional[str] = None

        self.logs: list[str] = []

    # =====================================================
    # LOGS
    # =====================================================

    def append_log(self, message: str):

        self.logs.append(message.rstrip())

        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]

    # =====================================================
    # PORTS
    # =====================================================

    def is_port_busy(self, port: int) -> bool:

        with socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM,
        ) as sock:

            return (
                sock.connect_ex(
                    ("127.0.0.1", port)
                ) == 0
            )

    def find_free_port(
        self,
        start: int = 3000,
    ) -> int:

        port = start

        while self.is_port_busy(port):
            port += 1

        return port

    # =====================================================
    # PROCESS
    # =====================================================

    def kill_process_tree(self, pid: int):

        try:
            os.killpg(
                os.getpgid(pid),
                signal.SIGTERM,
            )

        except Exception:
            pass

    # =====================================================
    # LOG STREAM
    # =====================================================

    def stream_logs(self, process):

        try:

            if process.stdout:

                for line in process.stdout:
                    self.append_log(line)

        except Exception as e:
            self.append_log(str(e))

    # =====================================================
    # STOP
    # =====================================================

    def stop_project(self):

        if self.process:

            try:
                self.kill_process_tree(
                    self.process.pid
                )

            except Exception:
                pass

        self.process = None
        self.pid = None
        self.port = None
        self.cwd = None
        self.command = None

        self.append_log("Project stopped")

        return {
            "status": "stopped",
        }

    # =====================================================
    # START
    # =====================================================

    def start_project(
        self,
        project_path: str,
    ):

        self.stop_project()

        frontend_dir = (
            Path(project_path)
            / "frontend"
        )

        if not frontend_dir.exists():

            return {
                "status": "error",
                "message": "Frontend folder not found",
            }

        package_json = (
            frontend_dir
            / "package.json"
        )

        if not package_json.exists():

            return {
                "status": "error",
                "message": "package.json not found",
            }

        port = self.find_free_port(3000)

        env = os.environ.copy()

        self.append_log(
            "Installing dependencies..."
        )

        install_process = subprocess.Popen(
            "npm install",
            cwd=str(frontend_dir),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        if install_process.stdout:

            for line in install_process.stdout:
                self.append_log(line)

        install_process.wait()

        self.append_log(
            "Starting Next.js server..."
        )

        process = subprocess.Popen(
            f"npm run dev -- --port {port}",
            cwd=str(frontend_dir),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid,
            env=env,
            bufsize=1,
        )

        self.process = process
        self.pid = process.pid
        self.port = port
        self.cwd = str(frontend_dir)

        self.command = (
            f"npm run dev -- --port {port}"
        )

        self.logs = []

        threading.Thread(
            target=self.stream_logs,
            args=(process,),
            daemon=True,
        ).start()

        time.sleep(5)

        running = process.poll() is None

        if running:

            self.append_log(
                f"Project running on http://localhost:{port}"
            )

        else:

            self.append_log(
                "Failed to start project"
            )

        return {
            "status": (
                "running"
                if running
                else "error"
            ),
            "pid": process.pid,
            "port": port,
            "url": f"http://localhost:{port}",
            "running": running,
        }

    # =====================================================
    # RESTART
    # =====================================================

    def restart_project(self):

        if not self.cwd:

            return {
                "status": "error",
                "message": "No active project",
            }

        project_root = str(
            Path(self.cwd).parent
        )

        self.stop_project()

        return self.start_project(project_root)

    # =====================================================
    # STATUS
    # =====================================================

    def get_runtime_status(self):

        if not self.process:

            return {
                "running": False,
            }

        running = (
            self.process.poll() is None
        )

        return {
            "running": running,
            "pid": self.pid,
            "command": self.command,
            "cwd": self.cwd,
            "port": self.port,
            "url": (
                f"http://localhost:{self.port}"
            ),
        }

    # =====================================================
    # LOGS
    # =====================================================

    def get_runtime_logs(self):

        return {
            "logs": self.logs[-300:],
        }


# =========================================================
# SINGLETON
# =========================================================

runtime_manager = RuntimeManager()


# =========================================================
# EXPORTS
# =========================================================

start_project = runtime_manager.start_project

stop_project = runtime_manager.stop_project

restart_project = runtime_manager.restart_project

get_runtime_status = (
    runtime_manager.get_runtime_status
)

get_runtime_logs = (
    runtime_manager.get_runtime_logs
)