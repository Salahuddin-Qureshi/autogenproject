# Presentation Guide — AutoGen: Agent → MCP → Orchestration

## What we built (big picture)
```
Customer ──► [ProductAgent] ──► [InventoryAgent] ──► [OrderAgent] ──► [DeliveryAgent] ──► DONE
                                       │
                                       ▼ (MCP)
                               [Shop MCP Server]
                               tool: check_stock
```
3 small programs, each one builds on the previous:

| File | Teaches |
|---|---|
| `0_simple_agent.py` | What an agent is |
| `shop_mcp_server.py` + `1_mcp_demo.py` | How an agent uses tools through MCP |
| `2_orchestration_demo.py` | How 4 agents work together |

## Libraries used
| Library | Why |
|---|---|
| `autogen-agentchat` | High-level AutoGen API: `AssistantAgent`, teams, termination |
| `autogen-ext[openai,mcp]` | Extensions: OpenAI model client + MCP connector |
| `mcp` | Official MCP library — we use `FastMCP` to build our server |
| `python-dotenv` | Loads the API key from the `.env` file |

(AutoGen has 3 layers: **Core API** (low level), **AgentChat API** (what we use), **Extensions API** (models, MCP, tools).)

---

## STEP 1 — Simple agent (`0_simple_agent.py`)
**Say:** "An agent = an LLM brain + instructions + (optionally) tools."
1. `OpenAIChatCompletionClient(model="gpt-4o-mini")` → the brain.
2. `AssistantAgent(name, model_client, system_message)` → the agent with its role.
3. `await agent.run(task=...)` → give it work, read the last message.

Run: `.venv/bin/python 0_simple_agent.py`

## STEP 2 — MCP (`shop_mcp_server.py` + `1_mcp_demo.py`)
**Say:** "MCP (Model Context Protocol) is like a USB port for agents. Write tools once in a server; any agent — AutoGen, Microsoft Agent Framework, Claude — can plug in."

Server side (`shop_mcp_server.py`):
- `FastMCP("ShopServer")` creates the server.
- `@mcp.tool()` turns a normal Python function into a tool. The docstring tells the LLM what it does.
- `mcp.run()` — server talks over **stdio** (standard input/output).

Agent side (`1_mcp_demo.py`), 4 steps:
1. `StdioServerParams(...)` — how to start the server.
2. `mcp_server_tools(server)` — ask "what tools do you have?" → gets `check_stock`.
3. `AssistantAgent(tools=tools)` — give tools to the agent.
4. `agent.run(...)` — the LLM **decides by itself** to call `check_stock`.
`reflect_on_tool_use=True` → the agent turns the raw tool result into a nice sentence.

Run: `.venv/bin/python 1_mcp_demo.py` → "Yes, we have 5 laptops in stock."

## STEP 3 — Orchestration (`2_orchestration_demo.py`)
**Say:** "Orchestration = deciding which agent works when. Like a manager running a team."
- 4 agents, each with **one job** (its `system_message`).
- Only InventoryAgent gets the MCP tools (least privilege).
- `RoundRobinGroupChat` = agents take turns in a fixed order; all share one conversation.
- Termination = when to stop:
  - `TextMentionTermination("DONE")` → stop when an agent says DONE.
  - `MaxMessageTermination(10)` → safety limit so agents never loop forever.
  - `|` means "OR".

Run both cases live:
```
.venv/bin/python 2_orchestration_demo.py "I want to buy a laptop, deliver to Sukkur."
.venv/bin/python 2_orchestration_demo.py "I want to buy a phone, deliver to Karachi."
```
Laptop → full flow → delivery confirmed. Phone (stock 0) → Inventory says DONE → stops early (**conditional ending**).

Other AutoGen team types (just mention):
- `SelectorGroupChat` — the LLM chooses who speaks next.
- `Swarm` — agents hand off to each other.

## Real lesson we learned while building (great to tell the class!)
Our first version **looped forever** — agents kept asking each other "what delivery date?".
We fixed it by: (1) strict instructions "never ask questions", (2) `MaxMessageTermination` safety limit.
→ This is exactly why Microsoft Agent Framework adds **explicit workflows**: steps & conditions are defined in code, not left to the LLM.

## Link to MAF (my topic)
- AutoGen orchestration = **conversation** (LLM-driven turns).
- MAF orchestration = **workflow graph** (explicit edges, conditions, checkpoints, human approval).
- The same MCP server works in both — that is the power of MCP.

## Likely questions
- **Why MCP, not a normal Python function?** Reusable across frameworks and apps; server can run separately/remotely.
- **Who decides to call the tool?** The LLM, based on the tool name + docstring.
- **What if agents never stop?** Termination conditions — we use DONE + max 10 messages.
- **Why 4 agents not 1?** Each does one job → easier to debug, safer (only Inventory can touch stock).
- **Where is the API key?** In `.env`, loaded by `python-dotenv`, never written in code.

## Setup on a new computer
```
cd demo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
# put OPENAI_API_KEY=... in a .env file
```
