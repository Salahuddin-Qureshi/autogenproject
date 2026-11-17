# MAF version of 2_orchestration_demo.py: same 4 agents, same MCP tool,
# coordinated as an explicit workflow graph instead of a round-robin chat.
# Run inside .venv_maf (separate from the AutoGen demo's .venv - mcp
# version conflict, see maf_shop_mcp_server.py).
import asyncio
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()  # reads OPENAI_API_KEY from the .env file

from agent_framework import Agent, AgentResponseUpdate, MCPStdioTool
from agent_framework.openai import OpenAIChatClient
from agent_framework.orchestrations import SequentialBuilder


async def main():
    client = OpenAIChatClient(model="gpt-4o-mini")  # same OPENAI_API_KEY as the AutoGen demo

    # Step 1: the same shop_mcp_server tool, started over stdio - only the
    # import path inside the server file changed for mcp 2.x (see that file).
    async with MCPStdioTool(
        name="shop",
        command=sys.executable,
        args=["maf_shop_mcp_server.py"],
    ) as shop_tool:
        # Step 2: four agents, each with ONE job - identical instructions to
        # the AutoGen version, so the only variable being compared is orchestration.
        product = Agent(
            client=client,
            name="ProductAgent",
            instructions=(
                "Our shop sells: laptop, phone, headphones. "
                "If the customer's message clearly asks for one of these, reply with ONLY "
                "that product name. If it does not (e.g. a greeting or small talk), reply "
                "with EXACTLY: NO_PRODUCT"
            ),
        )
        inventory = Agent(
            client=client,
            name="InventoryAgent",
            instructions=(
                "Check stock with the check_stock tool. "
                "If stock is 0, say 'Sorry, OUT OF STOCK.' Otherwise say 'In stock'."
            ),
            tools=shop_tool,
        )
        order = Agent(
            client=client,
            name="OrderAgent",
            instructions=(
                "Create the order yourself: make up an order ID and a price in PKR. "
                "Never ask the customer questions."
            ),
        )
        delivery_date = (date.today() + timedelta(days=3)).strftime("%d %B %Y")
        delivery = Agent(
            client=client,
            name="DeliveryAgent",
            instructions=(
                f"You are the delivery coordinator. In ONE short sentence, confirm delivery on "
                f"{delivery_date} by courier TCS to the customer's city. Do not repeat the order "
                "ID or price. Never ask questions."
            ),
        )

        task = " ".join(sys.argv[1:]) or "I want to buy a laptop, deliver to Sukkur."

        # Step 3: ProductAgent runs ALONE first, as plain Python control flow
        # decides what happens next - this is MAF's "functional" workflow
        # style (native if/else), used here because plain SequentialBuilder
        # has no built-in conditional branching: it always runs every
        # participant. Without this, a vague input like "hi" would get
        # hallucinated into a product and march through Inventory/Order/
        # Delivery as if it were a real order.
        print("[ProductAgent] ", end="", flush=True)
        product_result = await product.run(task)
        product_name = product_result.text.strip()
        print(product_name)

        if product_name == "NO_PRODUCT":
            print("[ProductAgent] I didn't catch a specific product in that - we sell "
                  "laptops, phones, and headphones. What would you like to order?")
            return

        # Step 4: the rest of the pipeline IS a graph - order is guaranteed
        # by SequentialBuilder, not by hoping three LLMs take turns correctly.
        # chain_only_agent_responses=True: each agent sees only the PREVIOUS
        # agent's reply, not the whole history - tighter context than AutoGen's
        # shared group chat, and it keeps DeliveryAgent from just repeating OrderAgent.
        workflow = SequentialBuilder(
            participants=[inventory, order, delivery],
            intermediate_output_from="all_other",  # show every agent's step, not just the last
            chain_only_agent_responses=True,
        ).build()

        next_task = f"The customer wants: {product_name}. Original request: {task}"

        # Step 5: stream real token deltas as each agent produces them.
        # Each agent's stream ends with one extra chunk repeating the whole
        # message (not a delta) - skip it when it matches what we already printed.
        last_author = None
        accumulated = ""
        async for event in workflow.run(next_task, stream=True):
            if event.type not in ("output", "intermediate") or not isinstance(event.data, AgentResponseUpdate):
                continue
            update = event.data
            author = update.author_name
            if not author:
                continue
            if author != last_author:
                print(f"\n[{author}] ", end="", flush=True)
                last_author, accumulated = author, ""
            if not update.text or update.text == accumulated:
                continue
            print(update.text, end="", flush=True)
            accumulated += update.text
        print()


if __name__ == "__main__":
    asyncio.run(main())
