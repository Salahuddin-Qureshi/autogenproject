# PART 2: Orchestration - 4 agents work together in order
import asyncio
import sys
from datetime import date, timedelta
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools

load_dotenv()  # reads OPENAI_API_KEY from the .env file


async def main():
    model = OpenAIChatCompletionClient(model="gpt-4o-mini", store=True)  # store=True -> visible in OpenAI Logs
    tools = await mcp_server_tools(StdioServerParams(command=sys.executable, args=["shop_mcp_server.py"]))

    # Each agent has ONE job
    product = AssistantAgent("ProductAgent", model_client=model,
        system_message="Our shop sells: laptop, phone, headphones. "
                       "If the customer's message clearly asks for one of these, reply with ONLY "
                       "that product name. If it does not (e.g. a greeting or small talk), reply "
                       "with EXACTLY: NO_PRODUCT")
    inventory = AssistantAgent("InventoryAgent", model_client=model, tools=tools,
        reflect_on_tool_use=True,
        system_message="Check stock with the check_stock tool. "
                       "If stock is 0, say 'Sorry, OUT OF STOCK. DONE'. Otherwise say 'In stock'.")
    order = AssistantAgent("OrderAgent", model_client=model,
        system_message="Create the order yourself: make up an order ID and a price in PKR. "
                       "Never ask the customer questions.")
    delivery_date = (date.today() + timedelta(days=3)).strftime("%d %B %Y")
    delivery = AssistantAgent("DeliveryAgent", model_client=model,
        system_message=f"Confirm delivery on {delivery_date} by courier TCS to the customer's city. "
                       "Never ask questions. End your message with DONE.")

    # The orchestrator: agents speak in turn (round robin)
    # Stop when someone says DONE, when ProductAgent can't find a product
    # (NO_PRODUCT - e.g. the customer just said "hi"), or after 10 messages
    # as a safety limit.
    team = RoundRobinGroupChat(
        [product, inventory, order, delivery],
        termination_condition=(
            TextMentionTermination("DONE")
            | TextMentionTermination("NO_PRODUCT")
            | MaxMessageTermination(10)
        ),
    )

    # The customer request can be typed on the command line
    task = " ".join(sys.argv[1:]) or "I want to buy a laptop, deliver to Karachi."
    await Console(team.run_stream(task=task))


asyncio.run(main())
