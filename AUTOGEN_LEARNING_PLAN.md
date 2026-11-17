# Learning Plan — AutoGen (AgentChat API)

**Goal:** go from "I know agentic AI concepts, but not AutoGen" to being able to confidently read, explain, extend and debug the three demo files in this folder (`0_simple_agent.py`, `shop_mcp_server.py` + `1_mcp_demo.py`, `2_orchestration_demo.py`) — and build new AutoGen agents/teams from scratch.

**Format:** each module = short concept explanation → read the real code in this repo → you make a small hands-on change → a checkpoint question before moving on. No module is just slides-in-chat; every module touches actual running code.

**Prerequisite assumed:** you already understand agentic AI concepts in general (agent = LLM + instructions + tools, multi-agent systems, why orchestration matters) from Person 1/2's material. We will **not** re-teach that — we start from "what does AutoGen specifically call these things, and how do I write it in code."

Progress tracking: tick boxes as we finish each module. This file is a living doc — update it as we go.

---

## Module 0 — Orientation (5 min)
- [ ] AutoGen's 3-layer architecture: **Core API** (low-level, event-driven actor runtime) vs **AgentChat API** (high-level, what we actually use) vs **Extensions API** (model clients, MCP, tools, third-party integrations).
- [ ] Where AutoGen sits relative to "just calling the OpenAI API yourself": what it automates (tool-call loop, multi-agent turn-taking, termination).
- [ ] Confirm the dev environment: `.venv` for AutoGen demos vs `.venv_maf` for the MAF demos — why they're separate (`mcp` version conflict).

**Checkpoint:** Explain in your own words what each of the 3 API layers is responsible for.

---

## Module 1 — A single agent (`0_simple_agent.py`)
- [ ] `OpenAIChatCompletionClient` — the model client abstraction; how AutoGen talks to any LLM provider through one interface.
- [ ] `AssistantAgent(name, model_client, system_message)` — anatomy of an agent object.
- [ ] `agent.run(task=...)` — what actually happens under the hood (one or more LLM calls, returns a `TaskResult`).
- [ ] `result.messages` — the message list shape: roles, content, what `messages[-1]` gives you vs the full `result`.
- [ ] **Hands-on:** change the system message to make the agent answer in a different persona or language; add a second `run()` call and see if/how memory persists (it won't, by default — why not, and what would fix that).

**Checkpoint:** What's the minimum set of things required to create a working AutoGen agent? What's missing if you want it to remember past turns?

---

## Module 2 — Tools, the plain-Python way
- [ ] How AutoGen converts a Python function into something an LLM can call (docstring + type hints = the tool schema).
- [ ] `tools=[...]` on `AssistantAgent`.
- [ ] `reflect_on_tool_use=True` vs `False` — what changes in the output when you flip it.
- [ ] **Hands-on:** write a tiny local Python function tool (no MCP) — e.g. `def convert_pkr_to_usd(amount: float) -> str`) — and give it to a fresh `AssistantAgent`. Watch it decide on its own to call it.

**Checkpoint:** Why does the LLM "decide" to call a tool — what information is it actually using to make that decision?

---

## Module 3 — MCP: tools as a separate server (`shop_mcp_server.py` + `1_mcp_demo.py`)
- [ ] What MCP is and why it exists (the "USB port for agents" framing, but now in your own words).
- [ ] Server side: `FastMCP("ShopServer")`, `@mcp.tool()`, docstrings as the tool's description, `mcp.run()` over stdio.
- [ ] Client side: `StdioServerParams` (how AutoGen launches the server process), `mcp_server_tools()` (tool discovery — it's a live handshake, not a static list).
- [ ] Why `tools=tools` here is just a list of auto-discovered tools, same shape as Module 2's manual tools.
- [ ] **Hands-on:** add a second tool to `shop_mcp_server.py` (e.g. `get_price(product: str) -> str`), re-run `1_mcp_demo.py`, and ask the agent a question that needs both tools in one turn.

**Checkpoint:** If you swapped this MCP server for a completely different one (e.g. a weather server), what — if anything — would you need to change in `1_mcp_demo.py`?

---

## Module 4 — Multi-agent orchestration (`2_orchestration_demo.py`)
- [ ] Why 4 single-job agents instead of 1 agent with a long system prompt (debuggability, least-privilege tool access).
- [ ] `RoundRobinGroupChat` — the turn-taking model; what "shared conversation" actually means (every agent sees every prior message).
- [ ] Termination conditions: `TextMentionTermination("DONE")`, `MaxMessageTermination(10)`, the `|` (OR) combinator.
- [ ] The real bug this repo hit (infinite loop before termination conditions were tightened) — read it as a case study in why termination design matters.
- [ ] `Console(team.run_stream(task=...))` — streaming vs the single `run()` from Module 1.
- [ ] **Hands-on:** run both the laptop and phone (`out of stock`) cases, then add a 5th agent (e.g. `FeedbackAgent` that asks the customer to rate the experience) to the round robin and observe where it inserts itself.

**Checkpoint:** Walk through, step by step, what happens from the moment you call `team.run_stream()` to the moment termination fires, for the "phone" (out-of-stock) case.

---

## Module 5 — Other team types (conceptual + light hands-on)
- [ ] `SelectorGroupChat` — an LLM picks the next speaker instead of a fixed order. When would you want this over round robin?
- [ ] `Swarm` — agents explicitly hand off to each other (`HandoffMessage`), vs implicit shared-conversation turn-taking.
- [ ] **Hands-on (optional, time permitting):** reimplement the 4-agent flow with `SelectorGroupChat` and compare behavior/cost to the round-robin version.

**Checkpoint:** Give one scenario where `SelectorGroupChat` would behave differently from `RoundRobinGroupChat` on the same 4 agents.

---

## Module 6 — Operating AutoGen in practice
- [ ] `store=True` on the model client → visible in OpenAI's own dashboard logs; why that matters for debugging multi-agent runs.
- [ ] AutoGen Studio: what it is (no-code/low-code UI over the same AgentChat concepts), when you'd reach for it vs writing code.
- [ ] Reading errors: common failure modes (tool schema mismatch, runaway loops, API key/env issues) and how to diagnose them from the message stream.

**Checkpoint:** None — this module is reference material you'll come back to while debugging later modules' hands-on exercises.

---

## Capstone — Extend the e-commerce demo yourself
Pick **one** (or more, if time allows) and implement it end-to-end, explaining your design choices:
- [ ] Add a `PaymentAgent` between Order and Delivery that "validates" a mock payment and can short-circuit the flow on failure.
- [ ] Add a human-in-the-loop step using AutoGen's `UserProxyAgent` so a real person approves the order before Delivery runs.
- [ ] Swap `RoundRobinGroupChat` for `SelectorGroupChat` and tune the selector prompt so it still reliably follows Product → Inventory → Order → Delivery order.
- [ ] Add a second MCP tool server (e.g. a mock payments server) and wire it only into the new `PaymentAgent` (least-privilege, same pattern as Inventory/MCP).

---

## Notes / running log
*(We'll jot down anything surprising, gotchas, or decisions here as we go — e.g. version quirks, API differences from docs, etc.)*
-
