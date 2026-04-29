from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.history import FileHistory
except ImportError:
    PromptSession = None  # type: ignore[assignment]
    FileHistory = None  # type: ignore[assignment]

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import track
    from rich.table import Table
except ImportError:
    Console = None  # type: ignore[assignment]
    Panel = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]

    def track(items, description=""):
        for item in items:
            yield item

from agent.config import AgentConfig, ensure_runtime_dirs
from agent.core.agent import AgentCore
from agent.core.executor import Executor
from agent.core.planner import Planner
from agent.core.reflector import Reflector
from agent.memory.long_term import LongTermMemory
from agent.memory.short_term import ShortTermMemory
from agent.tools.code_executor import build_code_executor
from agent.tools.file_tools import build_file_tools
from agent.tools.json_tool import build_json_tool
from agent.tools.memory_tool import build_memory_tool
from agent.tools.python_tool import build_python_tool
from agent.tools.registry import ToolRegistry
from agent.tools.shell_tools import build_shell_tool
from agent.tools.web_tools import build_web_tools

class BasicConsole:
    def print(self, message: Any) -> None:
        print(message)


console = Console() if Console else BasicConsole()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="coding-bye", description="Autonomous CLI agent workflow engine")
    parser.add_argument("--workspace", default="agent/workspace")
    parser.add_argument("--logs", default="agent/logs")
    parser.add_argument("--plugins", default="agent/plugins")
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--error-limit", type=int, default=5)
    parser.add_argument("--autonomous", action="store_true")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--base-url", default="https://api.openai.com/v1")
    return parser.parse_args()


def bootstrap(args: argparse.Namespace) -> AgentCore:
    root = Path(".").resolve()
    config = AgentConfig(
        base_url=args.base_url,
        model=args.model,
        api_key=os.getenv(args.api_key_env, ""),
        workspace_dir=(root / args.workspace).resolve(),
        logs_dir=(root / args.logs).resolve(),
        memory_db_path=(root / "agent/memory/long_term.db").resolve(),
        short_memory_path=(root / "agent/memory/short_term.json").resolve(),
        plugins_dir=(root / args.plugins).resolve(),
        max_steps=args.max_steps,
        error_limit=args.error_limit,
        autonomous_mode=args.autonomous,
    )
    ensure_runtime_dirs(config)

    registry = ToolRegistry()
    short_memory = ShortTermMemory(config.short_memory_path)
    long_memory = LongTermMemory(config.memory_db_path)

    def approve(command: str) -> bool:
        if not config.require_approval:
            return True
        answer = input(f"Approve shell command? '{command}' [y/N]: ").strip().lower()
        return answer in {"y", "yes"}

    for tool in build_file_tools(config.workspace_dir):
        registry.register(tool)
    for tool in build_web_tools():
        registry.register(tool)
    registry.register(build_shell_tool(config.workspace_dir, approve))
    registry.register(build_code_executor(config.workspace_dir))
    registry.register(build_json_tool())
    registry.register(build_python_tool())
    registry.register(build_memory_tool(long_memory))
    registry.load_plugins(config.plugins_dir)

    return AgentCore(
        config=config,
        planner=Planner(),
        executor=Executor(registry=registry, timeout_seconds=config.timeout_seconds),
        reflector=Reflector(),
        short_memory=short_memory,
        long_memory=long_memory,
    )


def show_tools(agent: AgentCore) -> None:
    if not Table:
        for tool in agent.executor.registry.list_tools():
            console.print(f"- {tool.name}: {tool.description}")
        return
    table = Table(title="Available Tools")
    table.add_column("Name")
    table.add_column("Description")
    for tool in agent.executor.registry.list_tools():
        table.add_row(tool.name, tool.description)
    console.print(table)


def show_plan(agent: AgentCore) -> None:
    if not Table:
        for task in agent.state.plan.tasks:
            console.print(f"{task.task_id}. [{task.status}] {task.description} (attempts={task.attempts})")
        return
    if not agent.state.plan:
        console.print("[yellow]No plan yet. Use /goal <text>[/yellow]")
        return
    table = Table(title="Current Plan")
    table.add_column("ID")
    table.add_column("Task")
    table.add_column("Status")
    table.add_column("Attempts")
    for task in agent.state.plan.tasks:
        table.add_row(str(task.task_id), task.description, task.status, str(task.attempts))
    console.print(table)


def render_trace(trace: dict[str, Any]) -> None:
    if not Panel:
        console.print(f"THOUGHT: {trace.get('thought', '')}")
        console.print(f"ACTION: {trace.get('action', '')}")
        console.print(f"RESULT: {trace.get('result', '')}")
        console.print(f"REFLECTION: {trace.get('reflection', '')}")
        return
    console.print(Panel(str(trace.get("thought", "")), title="THOUGHT"))
    console.print(Panel(str(trace.get("action", "")), title="ACTION"))
    console.print(Panel(str(trace.get("result", "")), title="RESULT"))
    console.print(Panel(str(trace.get("reflection", "")), title="REFLECTION"))


def repl(agent: AgentCore) -> int:
    history_file = agent.config.logs_dir / ".history"
    session = PromptSession(history=FileHistory(str(history_file))) if PromptSession and FileHistory else None
    mode = "command"
    console.print("[bold green]Coding Bye Agentic CLI[/bold green]")
    console.print("Use /goal, /plan, /run, /tools, /memory, /status, /reset, /mode, /exit")

    while True:
        raw = (session.prompt(f"[{mode}]> ") if session else input(f"[{mode}]> ")).strip()
        if not raw:
            continue
        if raw == "/exit":
            return 0
        if raw.startswith("/mode "):
            mode = raw.split(" ", 1)[1].strip()
            console.print(f"[cyan]Mode switched to {mode}[/cyan]")
            continue
        if raw.startswith("/goal "):
            agent.set_goal(raw.split(" ", 1)[1].strip())
            console.print("[green]Goal accepted and plan generated.[/green]")
            continue
        if raw == "/tools":
            show_tools(agent)
            continue
        if raw == "/plan":
            show_plan(agent)
            continue
        if raw == "/memory":
            console.print(agent.long_memory.summarize())
            continue
        if raw == "/status":
            console.print(
                {
                    "status": agent.state.status,
                    "goal": agent.state.goal,
                    "steps": agent.state.step_count,
                    "errors": agent.state.error_count,
                }
            )
            continue
        if raw == "/reset":
            agent.reset()
            console.print("[yellow]Agent state and short-term memory reset.[/yellow]")
            continue
        if raw == "/run":
            if mode == "agent" or agent.config.autonomous_mode:
                for _ in track(range(agent.config.max_steps), description="Autonomous execution..."):
                    result = agent.run_once()
                    if "trace" in result:
                        render_trace(result["trace"])
                    if result.get("done"):
                        break
                console.print(agent.run_until_done())
            else:
                result = agent.run_once()
                if "trace" in result:
                    render_trace(result["trace"])
            continue
        console.print("[red]Unknown command[/red]")


def main() -> int:
    args = parse_args()
    agent = bootstrap(args)
    return repl(agent)


if __name__ == "__main__":
    raise SystemExit(main())

