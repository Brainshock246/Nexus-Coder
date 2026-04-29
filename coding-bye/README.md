# Coding Bye Agentic CLI System

Coding Bye is now a true CLI agent workflow engine with explicit **think -> plan -> act -> observe -> reflect** cycles, persistent memory, modular tools, autonomous mode, plugin loading, and structured trace logs.

## Architecture

```
agent/
  cli/main.py
  core/{agent,planner,executor,reflector}.py
  tools/{file_tools,web_tools,shell_tools,json_tool,python_tool,code_executor,memory_tool}.py
  memory/{short_term,long_term}.py
  plugins/
  workspace/
  logs/
  config.py
```

## Features

- Goal-driven execution with dynamic planning and replanning.
- Modular tool system with automatic tool selection.
- Persistent memory:
  - Short-term (`agent/memory/short_term.json`)
  - Long-term SQLite (`agent/memory/long_term.db`)
- Reflection after every action (success/failure + improvement signal).
- Manual mode and autonomous mode.
- Safety controls:
  - Dangerous shell command filtering
  - Command approval prompts
  - Timeouts + retries
- Plugin auto-loading from `agent/plugins/*.py`.
- Trace logging in `agent/logs/agent.log`.

## Built-in commands

- `/goal <text>`
- `/tools`
- `/memory`
- `/plan`
- `/run`
- `/status`
- `/reset`
- `/mode command|agent`
- `/exit`

## Installation

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python coding_bye.py
```

Autonomous startup mode:

```bash
python coding_bye.py --autonomous --max-steps 30 --error-limit 8
```

## Plugin format

Create `agent/plugins/my_tool.py`:

```python
from agent.tools.base import Tool

def register(registry):
    registry.register(
        Tool(
            name="my_tool",
            description="Custom plugin tool",
            input_schema={"type": "object"},
            run=lambda payload: {"ok": True},
        )
    )
```

## Tests

```bash
python -m pytest -q
```
