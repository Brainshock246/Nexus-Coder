# Nexus-Coder: Elite Self-Evolving Agent CLI

Nexus-Coder is a production-grade autonomous CLI system with hierarchical multi-agent orchestration, persistent knowledge graph reasoning, self-healing execution, dynamic tool generation, compressed long-term memory, retrieval-augmented reasoning, reinforcement tool learning, and autonomous goal discovery.

## Architecture Diagram

```text
CLI (/goal, /run, /watch) 
   -> AgentCore (think -> plan -> act -> observe -> reflect)
      -> Planner + Prompt Engine
      -> Executor (LLM tool selection, scoring, retries, fallback, async)
      -> Reflector (replan signals)
      -> Memory
         -> short_term.json
         -> long_term.db
         -> task_graph.db (nodes/edges)
      -> Workspace Indexer (workspace_index.json)
      -> Logs (agent.log + session.json)
      -> Hierarchical Multi-Agent Layer (Supervisor->Planner->Executor->Reviewer->Optimizer)
      -> ToolRegistry + plugins
      -> Dynamic Tool Generator
      -> Knowledge Graph + Vector Retrieval
      -> Resource Monitor + Reward Learning
```

## Module Overview

- `agent/llm/`: provider abstraction (`LLMProvider`) + `OpenAIProvider` + `LocalProvider`.
- `agent/prompts/`: JSON-only prompt builders for planner/executor/reflector/tool selector.
- `agent/core/executor.py`: intelligent tool selection (LLM + scoring), validation, retries, timeout, fallback, async entrypoint, caching.
- `agent/workspace/indexer.py`: generates `workspace_index.json` with file metadata and relationships.
- `agent/memory/task_graph.py`: graph memory for goals/tasks/results and dependencies.
- `agent/core/reflector.py`: failure and repeated-error detection with replanning trigger.
- `agent/multi_agent/`: role and manager foundation for planner/executor/reviewer workers.
- `agent/multi_agent/hierarchy/`: supervisor-managed hierarchical orchestration roles.
- `agent/config.py`: dataclass config + `config.yaml` loading with overrides.
- `agent/knowledge/graph.py`: persistent knowledge graph with relationship discovery.
- `agent/rag/`: vector retrieval engine for files/memory/log context.
- `agent/learning/`: tool rewards, prompt evolution, and reusable skill templates.
- `agent/monitoring/resource_monitor.py`: CPU/memory/time guardrails.
- `agent/distributed/executor.py`: distributed execution foundation.

## CLI Commands

- `/goal <text>`: set goal and generate plan.
- `/plan`: inspect current plan.
- `/run`: execute step or autonomous loop.
- `/watch`: live trace viewer (thought/plan/action/result/reflection).
- `/tools`: list available tools.
- `/memory`: summarize long-term memory.
- `/roles`: show multi-agent role foundation.
- `/discover`: autonomous improvement goal suggestions.
- `/rewards`: learned tool ranking from reinforcement store.
- `/status`: current runtime status.
- `/reset`: reset state and short-term memory.
- `/exit`: exit CLI.

## Configuration

Use `config.yaml` (optional), plus CLI flags.

Example:

```yaml
provider: openai
model: gpt-4.1-mini
base_url: https://api.openai.com/v1
workspace: agent/workspace
logs: agent/logs
```

Provider options:
- `openai` (uses `OPENAI_API_KEY`)
- `local` (uses `local_model_url`, defaults to Ollama-compatible endpoint)

## Plugin Instructions

Create `agent/plugins/my_tool.py`:

```python
from agent.tools.base import Tool

def register(registry):
    registry.register(
        Tool(
            name="my_tool",
            description="Custom plugin",
            input_schema={"type": "object"},
            run=lambda payload: {"ok": True, "payload": payload},
        )
    )
```

## Example Usage

```bash
python -m pip install -r requirements.txt
python coding_bye.py --provider openai
```

Local model mode:

```bash
python coding_bye.py --provider local --model llama3.1
```

## Test Suite

```bash
python -m unittest discover -s tests -v
```
