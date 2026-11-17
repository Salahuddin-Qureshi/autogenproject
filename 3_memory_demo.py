# PART 3: Memory - giving an agent facts it should remember across runs,
# without the user having to repeat them every time.
import asyncio
from dotenv import load_dotenv

load_dotenv()  # reads OPENAI_API_KEY from the .env file

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType


async def main():
    # Step 1: a memory store - just a list of facts, kept in process memory.
    user_memory = ListMemory(name="customer_profile")
    await user_memory.add(MemoryContent(
        content="The customer always wants delivery to Sukkur.",
        mime_type=MemoryMimeType.TEXT,
    ))
    await user_memory.add(MemoryContent(
        content="The customer prefers replies in under 15 words.",
        mime_type=MemoryMimeType.TEXT,
    ))

    # Step 2: hand the memory to the agent. Before every model call, the
    # agent queries each memory in this list and injects the results into
    # the context the LLM sees - the agent's own code never asks for it.
    agent = AssistantAgent(
        name="ShopAssistant",
        model_client=OpenAIChatCompletionClient(model="gpt-4o-mini"),
        system_message="You are a shop assistant.",
        memory=[user_memory],
    )

    # Step 3: two SEPARATE run() calls - the second one never mentions
    # Sukkur or the word-limit rule, yet the agent still knows both.
    result1 = await agent.run(task="I want to buy a laptop.")
    print("Run 1:", result1.messages[-1].content)

    result2 = await agent.run(task="Where will it be delivered, and what's your reply-length rule?")
    print("Run 2:", result2.messages[-1].content)


asyncio.run(main())
