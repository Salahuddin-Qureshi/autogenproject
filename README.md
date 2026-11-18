# Multi-Agent Collaboration: AutoGen + Semantic Kernel → Microsoft Agent Framework

A hands-on companion to our class presentation *"Multi-Agent Collaboration: AutoGen and
Microsoft Agent Framework."* Instead of just describing how Microsoft's new **Agent
Framework (MAF)** grew out of **AutoGen** and **Semantic Kernel (SK)**, this repo builds
the *same* multi-agent system three times — once per SDK lineage — so the relationship
can be seen in running code, not just slides.

**The running example — Smart E-Commerce Order Management System:**
```
Customer ──► [ProductAgent] ──► [InventoryAgent] ──► [OrderAgent] ──► [DeliveryAgent] ──► DONE
                                       │
                                       ▼ (tool call)
                               check_stock(product)
```
Four single-purpose agents (find the product → check stock → create the order → confirm
delivery) coordinate to turn "I want to buy a laptop" into a completed order.

## Why "AutoGen + Semantic Kernel = MAF"

Microsoft positions Agent Framework as the convergence of its two earlier agent SDKs:
**AutoGen** (research-driven, conversation-first multi-agent orchestration) and
**Semantic Kernel** (production-driven, plugin/planner-based single-agent orchestration).
MAF keeps the parts of each that held up and unifies the rest:

| Concept in MAF | Carried forward from **AutoGen** | Carried forward from **Semantic Kernel** |
|---|---|---|
| `Agent` + `.run()` | `AssistantAgent` + `.run()` | `Kernel` + a chat completion service |
| Tools (`MCPStdioTool`, function tools) | MCP server integration (`mcp_server_tools`) | Plugins (`@kernel_function`) + automatic function-calling |
| Orchestration (`SequentialBuilder`, workflow graphs) | Multi-agent teams (`RoundRobinGroupChat`, `SelectorGroupChat`, `Swarm`) | Planners (goal → plan → execute) and explicit, inspectable control flow |
| Memory / state | `ListMemory`, injected model context | `ChatHistory`, kernel-level memory connectors |
| Production features | — | Middleware, checkpoints, human-in-the-loop, enterprise connectors |

In short: **AutoGen** proved that several specialized LLM agents talking to each other in
a shared conversation produces flexible, emergent behavior. **Semantic Kernel** proved
that giving an LLM typed, reliable, enterprise-ready building blocks (plugins, planners,
memory) makes that behavior safe to ship. **MAF** keeps AutoGen's multi-agent idea but
expresses it as an explicit **workflow graph** instead of a free-running conversation, and
keeps SK's **plugin/tool model** as its one unified way of giving agents capabilities.

## The demos

| # | File(s) | SDK | What it shows |
|---|---|---|---|
| 0 | [0_simple_agent.py](0_simple_agent.py) | AutoGen | The basic unit: an LLM + instructions = an agent |
| 1 | [shop_mcp_server.py](shop_mcp_server.py), [1_mcp_demo.py](1_mcp_demo.py) | AutoGen + MCP | Giving an agent a real tool over the Model Context Protocol |
| 2 | [2_orchestration_demo.py](2_orchestration_demo.py) | AutoGen | 4 agents, conversation-driven orchestration (`RoundRobinGroupChat` + termination conditions) |
| 3 | [3_memory_demo.py](3_memory_demo.py) | AutoGen | Facts that persist across separate `run()` calls (`ListMemory`) |
| 4 | [4_semantic_kernel_demo.py](4_semantic_kernel_demo.py) | Semantic Kernel | SK's plugin model (`@kernel_function`) + automatic function-calling — the ancestor of MAF's tool model |
| 5 | [maf_orchestration_demo.py](maf_orchestration_demo.py), [run_maf_backend.py](run_maf_backend.py) | Microsoft Agent Framework | The *same* 4 agents as #2, coordinated as an explicit `SequentialBuilder` workflow graph instead of a round-robin chat |
| — | [gui_app.py](gui_app.py) | AutoGen + MAF | A Gradio chat UI to run the e-commerce flow live and flip between the AutoGen and MAF orchestration backends |

Run #2 and #5 side by side with the same input and you can see the architectural
difference directly: AutoGen lets the agents negotiate turn order inside one shared
conversation (and needed explicit "never ask questions" guardrails + a message cap to
stay bounded — see [NOTES.md](NOTES.md)); MAF fixes the order and branching as code
(`SequentialBuilder` + an `if/else` for the "no product" case), so the structure doesn't
depend on the LLM behaving itself.

## Setup

Each SDK pins its own dependency versions (in particular `mcp` and `openai`), so each
demo runs in its own virtual environment:

```bash
# AutoGen demos (0-3)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Semantic Kernel demo (4)
python3 -m venv .venv_sk
.venv_sk/bin/pip install semantic-kernel python-dotenv

# Microsoft Agent Framework demos (maf_*, run_maf_backend.py)
python3 -m venv .venv_maf
.venv_maf/bin/pip install agent-framework agent-framework-openai agent-framework-orchestrations python-dotenv

# Gradio GUI (shells out to .venv / .venv_maf as subprocesses)
python3 -m venv .venv_gui
.venv_gui/bin/pip install gradio
```

Put your key in a `.env` file in this folder: `OPENAI_API_KEY=sk-...`

## Running it

```bash
.venv/bin/python 2_orchestration_demo.py "I want to buy a laptop, deliver to Sukkur."
.venv_sk/bin/python 4_semantic_kernel_demo.py
.venv_maf/bin/python maf_orchestration_demo.py "I want to buy a laptop, deliver to Sukkur."
.venv_gui/bin/python gui_app.py   # chat UI, pick the backend from a dropdown
```

## Further reading in this repo

- [NOTES.md](NOTES.md) — presentation walkthrough of the AutoGen demos, including the
  "agents looped forever" lesson that motivated MAF's explicit workflows.
- [MEMORY_IN_AGENTS.md](MEMORY_IN_AGENTS.md) — deeper dive on agent memory.
- [AUTOGEN_LEARNING_PLAN.md](AUTOGEN_LEARNING_PLAN.md) — the learning plan this repo was built from.
- [presentation.txt](presentation.txt) — the full class presentation outline this project supports.

---
Built for a university presentation on multi-agent collaboration (AutoGen & Microsoft
Agent Framework) by Salahuddin Qureshi's presentation group.
