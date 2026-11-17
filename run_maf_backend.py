# Headless runner for the MAF e-commerce flow, meant to be launched as a
# subprocess (one JSON line per agent message on stdout) by gui_app.py.
# Run directly for debugging: .venv_maf/bin/python run_maf_backend.py "task..."
import asyncio
import json
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()

from agent_framework import Agent, AgentResponseUpdate, MCPStdioTool
from agent_framework.openai import OpenAIChatClient
from agent_framework.orchestrations import SequentialBuilder


def emit(agent: str, text: str) -> None:
    if agent and text:
        print(json.dumps({"agent": agent, "text": text}), flush=True)


async def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "I want to buy a laptop, deliver to Sukkur."

    client = OpenAIChatClient(model="gpt-4o-mini")

    async with MCPStdioTool(
        name="shop", command=sys.executable, args=["maf_shop_mcp_server.py"],
    ) as shop_tool:
        product = Agent(
            client=client, name="ProductAgent",
            instructions="Our shop sells: laptop, phone, headphones. "
                         "Reply with ONLY the product name the customer wants.",
        )
        inventory = Agent(
            client=client, name="InventoryAgent",
            instructions="Check stock with the check_stock tool. "
                         "If stock is 0, say 'Sorry, OUT OF STOCK.' Otherwise say 'In stock'.",
            tools=shop_tool,
        )
        order = Agent(
            client=client, name="OrderAgent",
            instructions="Create the order yourself: make up an order ID and a price in PKR. "
                         "Never ask the customer questions.",
        )
        delivery_date = (date.today() + timedelta(days=3)).strftime("%d %B %Y")
        delivery = Agent(
            client=client, name="DeliveryAgent",
            instructions=f"You are the delivery coordinator. In ONE short sentence, confirm delivery on "
                         f"{delivery_date} by courier TCS to the customer's city. Do not repeat the order "
                         "ID or price. Never ask questions.",
        )

        workflow = SequentialBuilder(
            participants=[product, inventory, order, delivery],
            intermediate_output_from="all_other",
            chain_only_agent_responses=True,
        ).build()

        last_author = None
        accumulated = ""
        async for event in workflow.run(task, stream=True):
            if event.type not in ("output", "intermediate") or not isinstance(event.data, AgentResponseUpdate):
                continue
            update = event.data
            author = update.author_name
            if not author:
                continue
            if author != last_author:
                emit(last_author, accumulated)
                last_author, accumulated = author, ""
            if not update.text or update.text == accumulated:
                continue
            accumulated += update.text
        emit(last_author, accumulated)


if __name__ == "__main__":
    asyncio.run(main())
