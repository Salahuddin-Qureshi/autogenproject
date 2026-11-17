# Memory in AI Agents — AutoGen (and MAF, for comparison)

Companion code: [`3_memory_demo.py`](3_memory_demo.py) — tested and working (`.venv/bin/python 3_memory_demo.py`).

## Two different things both get called "memory" — don't mix them up

| | **Conversation history** (`model_context`) | **Memory** (`Memory` / `ListMemory`) |
|---|---|---|
| What it is | The raw back-and-forth of the *current* run | Facts the agent should know *regardless* of what's been said |
| Lifetime | One `run()` / one session | Survives across separate `run()` calls, even new processes if persisted |
| Who writes to it | The chat itself, automatically | You, explicitly (`memory.add(...)`) |
| Default in AutoGen | `UnboundedChatCompletionContext` — keeps everything | None — `memory=None` unless you pass one |

Both of these ultimately get merged into what the LLM sees, but they answer different questions: history answers *"what did we just say to each other,"* memory answers *"what should I always know about this user/situation."* The demo in this repo's `2_orchestration_demo.py` only ever used history (each agent sees the group chat so far); `3_memory_demo.py` is the first file in this repo that uses real `Memory`.

---

## 1. Conversation history — `model_context`

Every `AssistantAgent` has a `model_context` parameter (default `None` → `UnboundedChatCompletionContext`, i.e. "remember everything in this run"). AutoGen ships four implementations, all in `autogen_core.model_context`:

- **`UnboundedChatCompletionContext`** — keeps the full history. Default. Fine for short demos like ours; gets expensive/slow as a conversation grows.
- **`BufferedChatCompletionContext(buffer_size=N)`** — keeps only the last N messages.
- **`HeadAndTailChatCompletionContext(head_size, tail_size)`** — keeps the first few messages (often the system/task setup) plus the most recent few, dropping the middle.
- **`TokenLimitedChatCompletionContext(model_client, token_limit=...)`** — keeps as many recent messages as fit in a token budget.

This is about **truncating the current conversation**, not remembering things between separate runs. If you called `agent.run()` a second time with a brand-new agent object, none of this would carry over — that's what `Memory` is for.

## 2. Real memory — the `Memory` abstract class

`autogen_core.memory.Memory` is the interface:

```python
class Memory(ABC):
    async def add(self, content: MemoryContent, cancellation_token=None) -> None: ...
    async def query(self, query, cancellation_token=None, **kwargs) -> MemoryQueryResult: ...
    async def update_context(self, model_context: ChatCompletionContext) -> UpdateContextResult: ...
    async def clear(self) -> None: ...
    async def close(self) -> None: ...
```

The part that matters most for understanding the magic: **`update_context`**. You never call this yourself — `AssistantAgent` calls it on every memory object in its `memory=[...]` list, *before every single model call*, passing in the agent's own `model_context`. The memory decides what (if anything) to inject, and mutates the context the LLM is about to see. That's the entire mechanism behind "the agent just knows things."

### `ListMemory` — the built-in, simplest implementation

`ListMemory` just keeps an in-process Python list of `MemoryContent` objects and dumps *all* of them into context on every call (no relevance filtering — that's what the vector-store backed memories below are for).

```python
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType

user_memory = ListMemory(name="customer_profile")
await user_memory.add(MemoryContent(
    content="The customer always wants delivery to Sukkur.",
    mime_type=MemoryMimeType.TEXT,
))

agent = AssistantAgent(
    name="ShopAssistant",
    model_client=model_client,
    memory=[user_memory],   # <- this is the whole integration
)
```

`MemoryContent.mime_type` can be `TEXT`, `MARKDOWN`, `JSON`, `IMAGE`, or `BINARY` — it's just metadata about how to interpret `content`; AutoGen doesn't enforce anything based on it.

### What actually happens — verified output

Run twice, with a **brand-new task each time**, neither of which mentions Sukkur or any length rule:

```
Run 1 ("I want to buy a laptop."):
  "What specifications do you want for the laptop?"

Run 2 ("Where will it be delivered, and what's your reply-length rule?"):
  "Delivery will be to Sukkur. Replies should be under 15 words."
```

The agent answers Run 2 correctly even though *that specific run* never said "Sukkur" — because `ListMemory.update_context` re-injected both facts into the model's context before the call. Swap `ListMemory` for a vector-backed memory (below) and the same `memory=[...]` line of agent code doesn't change at all — only what's injected gets smarter.

### Beyond `ListMemory` — pluggable backends (`autogen_ext.memory`)

Same `Memory` interface, different storage/retrieval strategy, each needing its own optional install:

| Class | Package extra | What's different from `ListMemory` |
|---|---|---|
| `ChromaDBVectorMemory` | `pip install autogen-ext[chromadb]` | Embeds facts, retrieves only the *semantically relevant* ones on `query()` instead of dumping everything |
| `Mem0Memory` | `pip install autogen-ext[mem0]` | Delegates to the Mem0 service/library — automatic fact extraction, de-duplication, long-term user profiles |
| `RedisMemory` | `pip install autogen-ext[redisvl]` | Vector search backed by Redis — for memory that needs to survive process restarts and be shared across agent instances |

This repo only has `ListMemory` installed/tested (no extra network service needed) — the others are worth knowing *exist* for a "why would I need a vector database for this" question, but weren't exercised here.

---

## How this maps to MAF (what you already have in the Person 3 slide deck)

MAF doesn't call anything "Memory" — the nearest equivalents are two different pieces, which actually maps cleanly onto the table above:

- **`AgentSession`** ≈ AutoGen's `model_context`. Multi-turn conversation state for *one agent*, within one logical interaction. See the `state-management` slide.
- **Checkpointing** (superstep-boundary persistence of executor state) ≈ the durability angle of `Memory`, but at the *workflow* level, not the per-agent fact level. It's built for "resume this exact workflow run," not "remember this user's preferences forever."
- MAF has **context providers** (mentioned on the `architecture` slide's foundational building blocks row) as the closer analogue to AutoGen's `Memory` — pluggable components that feed an agent long-term context — but we didn't build or test one for this project, unlike `ListMemory` here, so treat that as a pointer for further reading, not a verified claim.

**One-line contrast to say out loud if asked:** *"AutoGen's `Memory` is a small, explicit, per-agent interface you plug facts into directly; MAF pushes the same idea up into session/checkpoint infrastructure designed for whole workflows, not just one agent's recall."*

---

## Try it yourself (extends `AUTOGEN_LEARNING_PLAN.md`)

- [ ] Run `3_memory_demo.py` yourself, then change the second fact to something that conflicts with an instruction in `system_message` — see which one the model follows.
- [ ] Add `memory=[user_memory]` to `InventoryAgent` in `2_orchestration_demo.py` with a fact like "This customer is a VIP, always say stock is reserved for them" and see how it changes the out-of-stock phone case.
- [ ] (Optional, needs `pip install autogen-ext[chromadb]`) Swap `ListMemory` for `ChromaDBVectorMemory` with 10+ facts and watch `query()` return only the relevant ones instead of all of them.
