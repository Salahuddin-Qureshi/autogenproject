# Gradio GUI shell for the e-commerce demo. Runs under .venv_gui.
# It does NOT import autogen_agentchat or agent_framework itself - each
# backend has its own venv (mcp version conflict), so this app shells out
# to the right interpreter as a subprocess and streams its JSON-lines output.
import json
import subprocess
import sys
from pathlib import Path

import gradio as gr

DEMO_DIR = Path(__file__).parent

BACKENDS = {
    "AutoGen (RoundRobinGroupChat)": {
        "python": str(DEMO_DIR / ".venv" / "bin" / "python"),
        "script": "run_autogen_backend.py",
    },
    "Microsoft Agent Framework (SequentialBuilder)": {
        "python": str(DEMO_DIR / ".venv_maf" / "bin" / "python"),
        "script": "run_maf_backend.py",
    },
}

AGENT_EMOJI = {
    "user": "🧑",
    "ProductAgent": "🛒",
    "InventoryAgent": "📦",
    "OrderAgent": "🧾",
    "DeliveryAgent": "🚚",
}


def run_backend(backend_name: str, task: str, history: list[dict]):
    history = history + [{"role": "user", "content": task}]
    yield history, ""

    backend = BACKENDS[backend_name]
    python_bin = Path(backend["python"])
    if not python_bin.exists():
        history.append({
            "role": "assistant",
            "content": f"⚠️ Interpreter not found: {python_bin}\n\nDid you create that venv? "
                       f"(see NOTES.md / AUTOGEN_LEARNING_PLAN.md)",
        })
        yield history, ""
        return

    process = subprocess.Popen(
        [str(python_bin), backend["script"], task],
        cwd=DEMO_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    saw_agent_message = False
    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue  # ignore any stray non-JSON stdout noise
        agent, text = msg.get("agent"), msg.get("text")
        if not agent or not text or agent == "user":
            continue
        saw_agent_message = True
        emoji = AGENT_EMOJI.get(agent, "🤖")
        history.append({"role": "assistant", "content": f"{emoji} **{agent}**\n\n{text}"})
        yield history, ""

    process.wait()
    if process.returncode != 0:
        stderr_tail = (process.stderr.read() or "").strip().splitlines()
        err_detail = "\n".join(stderr_tail[-15:]) if stderr_tail else "(no stderr captured)"
        history.append({
            "role": "assistant",
            "content": f"⚠️ Backend exited with code {process.returncode}.\n```\n{err_detail}\n```",
        })
        yield history, ""
    elif not saw_agent_message:
        history.append({"role": "assistant", "content": "⚠️ No agent messages were produced - check your OPENAI_API_KEY in .env."})
        yield history, ""


with gr.Blocks(title="Smart E-Commerce Order Assistant") as demo:
    gr.Markdown(
        "# 🛍️ Smart E-Commerce Order Assistant\n"
        "Product → Inventory → Order → Delivery, run by **either** AutoGen or "
        "Microsoft Agent Framework. Same MCP stock-check tool underneath both."
    )
    backend_choice = gr.Radio(
        choices=list(BACKENDS.keys()),
        value=list(BACKENDS.keys())[0],
        label="Orchestration backend",
    )
    chatbot = gr.Chatbot(height=480, label="Conversation")
    with gr.Row():
        task_box = gr.Textbox(
            placeholder="e.g. I want to buy a laptop, deliver to Sukkur.",
            label="Customer request",
            scale=4,
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)
    clear_btn = gr.Button("Clear conversation")

    def on_submit(backend_name, task, history):
        if not task.strip():
            yield history, task
            return
        yield from run_backend(backend_name, task, history or [])

    send_btn.click(on_submit, [backend_choice, task_box, chatbot], [chatbot, task_box])
    task_box.submit(on_submit, [backend_choice, task_box, chatbot], [chatbot, task_box])
    clear_btn.click(lambda: ([], ""), None, [chatbot, task_box])

if __name__ == "__main__":
    demo.launch()
