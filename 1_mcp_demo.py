# PART 1: How an AutoGen agent connects to an MCP server
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()  # reads OPENAI_API_KEY from the .env file
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools


async def main():
    # Step 1: tell AutoGen how to start the MCP server
    server = StdioServerParams(command=sys.executable, args=["shop_mcp_server.py"])

    # Step 2: ask the server which tools it has
    tools = await mcp_server_tools(server)

    # Step 3: give those tools to an agent
    inventory_agent = AssistantAgent(
        name="InventoryAgent",
        model_client=OpenAIChatCompletionClient(model="gpt-4o-mini", store=True),  # store=True -> visible in OpenAI Logs
        tools=tools,
        reflect_on_tool_use=True,  # turn the tool result into a nice sentence
        system_message="You check product stock using your tools.",
    )

    # Step 4: ask a question - the agent calls the MCP tool by itself
    result = await inventory_agent.run(task="Do we have laptops in stock?")
    print(result.messages[-1].content)


asyncio.run(main())
