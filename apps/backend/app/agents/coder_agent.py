from __future__ import annotations

import json
from pathlib import Path

import ollama

from app.memory.agent_memory import agent_memory
from app.tools.file_tool import save_file
from app.tools.project_tool import create_project_structure
from app.tools.shell_tool import run_command


def _build_frontend_layout(title: str) -> str:
    safe_title = title.replace('"', "'")

    return f"""import type {{ Metadata }} from "next";
import type {{ ReactNode }} from "react";
import "./globals.css";

export const metadata: Metadata = {{
  title: "{safe_title}",
  description: "AI generated startup project",
}};

export default function RootLayout({{
  children,
}}: Readonly<{{ children: ReactNode }}>) {{
  return (
    <html lang="ru">
      <body>{{children}}</body>
    </html>
  );
}}
"""


def _build_frontend_page(title: str, description: str) -> str:
    title_json = json.dumps(title, ensure_ascii=False)
    description_json = json.dumps(description, ensure_ascii=False)

    return f"""const title = {title_json};
const description = {description_json};

const stats = [
  {{
    label: "Active Users",
    value: "12K+",
  }},
  {{
    label: "Revenue",
    value: "$84K",
  }},
  {{
    label: "Growth",
    value: "+34%",
  }},
];

const features = [
  {{
    title: "AI Automation",
    text: "Автоматизация бизнес процессов и AI workflows.",
  }},
  {{
    title: "Analytics",
    text: "Подробная аналитика и dashboard система.",
  }},
  {{
    title: "CRM System",
    text: "Полноценное управление клиентами.",
  }},
  {{
    title: "Scalable Architecture",
    text: "Готовность к росту и высоким нагрузкам.",
  }},
];

export default function Home() {{
  return (
    <main
      style={{{{
        minHeight: "100vh",
        background: "#050816",
        color: "white",
        fontFamily:
          'Inter, system-ui, sans-serif',
      }}}}
    >
      <section
        style={{{{
          maxWidth: "1400px",
          margin: "0 auto",
          padding: "80px 32px",
        }}}}
      >
        <div
          style={{{{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "80px",
          }}}}
        >
          <div
            style={{{{
              fontSize: "28px",
              fontWeight: 800,
            }}}}
          >
            AI OS
          </div>

          <div
            style={{{{
              display: "flex",
              gap: "16px",
            }}}}
          >
            <button
              style={{{{
                padding: "14px 22px",
                borderRadius: "14px",
                border: "1px solid #1e293b",
                background: "transparent",
                color: "white",
                cursor: "pointer",
              }}}}
            >
              Login
            </button>

            <button
              style={{{{
                padding: "14px 22px",
                borderRadius: "14px",
                border: "none",
                background: "#22c55e",
                color: "black",
                fontWeight: 700,
                cursor: "pointer",
              }}}}
            >
              Get Started
            </button>
          </div>
        </div>

        <div
          style={{{{
            display: "grid",
            gridTemplateColumns: "1.2fr 0.8fr",
            gap: "40px",
            alignItems: "center",
            marginBottom: "80px",
          }}}}
        >
          <div>
            <div
              style={{{{
                display: "inline-flex",
                padding: "10px 16px",
                borderRadius: "999px",
                background: "rgba(34,197,94,0.12)",
                color: "#22c55e",
                marginBottom: "24px",
              }}}}
            >
              AI GENERATED STARTUP
            </div>

            <h1
              style={{{{
                fontSize: "72px",
                lineHeight: 1,
                fontWeight: 900,
                marginBottom: "28px",
              }}}}
            >
              {{title}}
            </h1>

            <p
              style={{{{
                fontSize: "20px",
                color: "#94a3b8",
                lineHeight: 1.8,
                marginBottom: "40px",
              }}}}
            >
              {{description}}
            </p>

            <div
              style={{{{
                display: "flex",
                gap: "18px",
              }}}}
            >
              <button
                style={{{{
                  padding: "18px 28px",
                  borderRadius: "18px",
                  border: "none",
                  background: "#06b6d4",
                  color: "black",
                  fontWeight: 800,
                  fontSize: "16px",
                  cursor: "pointer",
                }}}}
              >
                Launch Platform
              </button>

              <button
                style={{{{
                  padding: "18px 28px",
                  borderRadius: "18px",
                  border: "1px solid #334155",
                  background: "transparent",
                  color: "white",
                  fontWeight: 700,
                  cursor: "pointer",
                }}}}
              >
                Watch Demo
              </button>
            </div>
          </div>

          <div
            style={{{{
              background: "linear-gradient(180deg,#111827,#020617)",
              border: "1px solid #1e293b",
              borderRadius: "32px",
              padding: "32px",
            }}}}
          >
            <div
              style={{{{
                fontSize: "22px",
                fontWeight: 700,
                marginBottom: "28px",
              }}}}
            >
              Platform Metrics
            </div>

            <div
              style={{{{
                display: "grid",
                gap: "20px",
              }}}}
            >
              {{stats.map((item) => (
                <div
                  key={{item.label}}
                  style={{{{
                    padding: "24px",
                    borderRadius: "22px",
                    background: "#0f172a",
                  }}}}
                >
                  <div
                    style={{{{
                      color: "#94a3b8",
                      marginBottom: "12px",
                    }}}}
                  >
                    {{item.label}}
                  </div>

                  <div
                    style={{{{
                      fontSize: "42px",
                      fontWeight: 900,
                    }}}}
                  >
                    {{item.value}}
                  </div>
                </div>
              ))}}
            </div>
          </div>
        </div>

        <div
          style={{{{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit,minmax(260px,1fr))",
            gap: "24px",
          }}}}
        >
          {{features.map((feature) => (
            <div
              key={{feature.title}}
              style={{{{
                padding: "32px",
                borderRadius: "28px",
                background: "#0f172a",
                border: "1px solid #1e293b",
              }}}}
            >
              <div
                style={{{{
                  fontSize: "24px",
                  fontWeight: 800,
                  marginBottom: "18px",
                }}}}
              >
                {{feature.title}}
              </div>

              <div
                style={{{{
                  color: "#94a3b8",
                  lineHeight: 1.8,
                }}}}
              >
                {{feature.text}}
              </div>
            </div>
          ))}}
        </div>
      </section>
    </main>
  );
}}
"""


def _build_frontend_globals() -> str:
    return """html, body {
  margin: 0;
  padding: 0;
  background: #000000;
  color: #ffffff;
}

* {
  box-sizing: border-box;
}

a {
  color: inherit;
  text-decoration: none;
}
"""


def _build_frontend_package_json(project_name: str) -> str:
    return json.dumps(
        {
            "name": project_name,
            "private": True,
            "version": "0.1.0",
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
            },
            "dependencies": {
                "next": "^16.2.6",
                "react": "^19.0.0",
                "react-dom": "^19.0.0",
            },
            "devDependencies": {
                "@types/node": "^22.15.0",
                "@types/react": "^19.0.10",
                "@types/react-dom": "^19.0.4",
                "typescript": "^5.8.3",
            },
        },
        ensure_ascii=False,
        indent=2,
    )


def _build_frontend_tsconfig() -> str:
    return """{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
"""


def _build_next_config() -> str:
    return """/** @type {import("next").NextConfig} */
const nextConfig = {};

export default nextConfig;
"""


def _build_frontend_readme(project_name: str) -> str:
    return f"""# {project_name}

Generated by AI OS.

## Run

```bash
npm install
npm run dev
```
"""


def _build_run_script() -> str:
    return """#!/usr/bin/env bash
set -e

cd frontend
npm install
npm run dev
"""


def _build_gitignore() -> str:
    return """node_modules
.next
dist
.DS_Store
"""


def _build_architecture_doc(task: str, research: str, architecture: str) -> str:
    return f"""# Architecture

## Task

{task}

## Research

{research}

## Architecture

{architecture}
"""


def coder_agent(
    task: str,
    architecture: str,
    research: str,
) -> dict[str, object]:
    agent_memory["coder"].update(
        {
            "status": "working",
            "task": "Генерация проекта",
            "phase": "writing",
        }
    )
    agent_memory["active_agent"] = "coder"

    prompt = f"""
Ты senior AI engineer.

Создай структурированный markdown-отчет по стартапу.

Задача:
{task}

Исследование:
{research}

Архитектура:
{architecture}

Сделай разделы:

AI STARTUP REPORT
Idea
MVP
Tech Stack
Architecture
Marketing
Risks
Roadmap

Пиши на русском языке, четко и структурированно.
""".strip()

    try:
        response = ollama.chat(
            model="phi3:mini",
            messages=[
                {
                    "role": "system",
                    "content": "Отвечай только на русском языке.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": 0.4,
                "num_predict": 1200,
            },
        )
        report_content = response.get("message", {}).get("content", "").strip()
    except Exception as e:
        report_content = f"Ошибка Coder Agent: {str(e)}"

    agent_memory["coder"].update(
        {
            "status": "saving",
            "task": "Сохранение проекта",
            "phase": "saving",
        }
    )

    project = create_project_structure(task)
    project_folder = Path(project["project_folder"])
    project_name = project["project_name"]

    frontend_folder = project_folder / "frontend"
    backend_folder = project_folder / "backend"
    docs_folder = project_folder / "docs"
    reports_folder = project_folder / "reports"

    saved_files: list[str] = []

    saved_files.append(
        save_file(
            str(project_folder / "README.md"),
            f"# {project_name}\n\n{task}\n",
        )
    )

    saved_files.append(
        save_file(
            str(project_folder / "project.json"),
            json.dumps(
                {
                    "task": task,
                    "research": research,
                    "architecture": architecture,
                    "project_name": project_name,
                    "project_folder": str(project_folder),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    )

    saved_files.append(
        save_file(
            str(project_folder / ".gitignore"),
            _build_gitignore(),
        )
    )

    saved_files.append(
        save_file(
            str(project_folder / "run.sh"),
            _build_run_script(),
        )
    )

    saved_files.append(
        save_file(
            str(frontend_folder / "package.json"),
            _build_frontend_package_json(project_name),
        )
    )

    saved_files.append(
        save_file(
            str(frontend_folder / "tsconfig.json"),
            _build_frontend_tsconfig(),
        )
    )

    saved_files.append(
        save_file(
            str(frontend_folder / "next.config.mjs"),
            _build_next_config(),
        )
    )

    saved_files.append(
        save_file(
            str(frontend_folder / "README.md"),
            _build_frontend_readme(project_name),
        )
    )

    saved_files.append(
        save_file(
            str(frontend_folder / "app" / "layout.tsx"),
            _build_frontend_layout(project_name),
        )
    )

    title_line = task.strip().splitlines()[0].strip() if task.strip() else "AI Startup"
    description_line = (
        architecture.splitlines()[0].strip()
        if architecture.strip()
        else "Generated by AI OS."
    )

    saved_files.append(
        save_file(
            str(frontend_folder / "app" / "page.tsx"),
            _build_frontend_page(title_line, description_line),
        )
    )

    saved_files.append(
        save_file(
            str(frontend_folder / "app" / "globals.css"),
            _build_frontend_globals(),
        )
    )

    saved_files.append(
        save_file(
            str(docs_folder / "architecture.md"),
            _build_architecture_doc(task, research, architecture),
        )
    )

    saved_files.append(
        save_file(
            str(reports_folder / "report.md"),
            report_content,
        )
    )

    shell_result = run_command(
        "git init",
        cwd=str(project_folder),
    )

    agent_memory["project_tree"] = saved_files
    agent_memory["last_saved_project"] = {
        "folder": str(project_folder),
        "files": saved_files,
        "project_name": project_name,
        "shell": shell_result,
        "frontend_folder": str(frontend_folder),
        "backend_folder": str(backend_folder),
    }

    agent_memory["coder"].update(
        {
            "status": "done",
            "task": "Проект сохранен",
            "phase": "idle",
        }
    )
    agent_memory["active_agent"] = "none"

    return {
        "content": report_content,
        "saved": agent_memory["last_saved_project"],
    }