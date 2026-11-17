# PART 0: The simplest AutoGen agent (an LLM + instructions)
import asyncio
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

load_dotenv()  # reads OPENAI_API_KEY from the .env file


async def main():
    # Step 1: choose the brain (the LLM)
    model = OpenAIChatCompletionClient(model="gpt-4o-mini")

    # Step 2: create the agent = name + brain + instructions
    product_agent = AssistantAgent(
        name="ProductAgent",
        model_client=model,
        system_message="You are a shop assistant. Recommend one product in one sentence.",
    )

    # Step 3: give it a task and print the answer
    result = await product_agent.run(task="I need something to listen to music while jogging.")
    print(result.messages[-1].content)
    print(result)
        


asyncio.run(main())
