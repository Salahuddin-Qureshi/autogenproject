# Headless runner for the AutoGen e-commerce flow, meant to be launched as a
# subprocess (one JSON line per agent message on stdout) by gui_app.py.
# Run directly for debugging: .venv/bin/python run_autogen_backend.py "task..."
import asyncio
import json
import sys
from datetime import date, timedelta

from dotenv import load_dotenv

load_dotenv()

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools


async def main():
    task = sys.argv[1] if len(sys.argv) > 1 else "I want to buy a laptop, deliver to Sukkur."

    model = OpenAIChatCompletionClient(model="gpt-4o-mini")
    tools = await mcp_server_tools(StdioServerParams(command=sys.executable, args=["shop_mcp_server.py"]))

    product = AssistantAgent(
        "ProductAgent", model_client=model,
        system_message="Our shop sells: laptop, phone, headphones. "
                        "Reply with ONLY the product name the customer wants.",
    )
    inventory = AssistantAgent(
        "InventoryAgent", model_client=model, tools=tools, reflect_on_tool_use=True,
        system_message="Check stock with the check_stock tool. "
                        "If stock is 0, say 'Sorry, OUT OF STOCK. DONE'. Otherwise say 'In stock'.",
    )
    order = AssistantAgent(
        "OrderAgent", model_client=model,
        system_message="Create the order yourself: make up an order ID and a price in PKR. "
                        "Never ask the customer questions.",
    )
    delivery_date = (date.today() + timedelta(days=3)).strftime("%d %B %Y")
    delivery = AssistantAgent(
        "DeliveryAgent", model_client=model,
        system_message=f"Confirm delivery on {delivery_date} by courier TCS to the customer's city. "
                        "Never ask questions. End your message with DONE.",
    )

    team = RoundRobinGroupChat(
        [product, inventory, order, delivery],
        termination_condition=TextMentionTermination("DONE") | MaxMessageTermination(10),
    )

    async for message in team.run_stream(task=task):
        source = getattr(message, "source", None)
        content = getattr(message, "content", None)
        if source and isinstance(content, str) and content.strip():
            print(json.dumps({"agent": source, "text": content}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
