# PART 4: Semantic Kernel - the other half of MAF's parentage.
# Same shop, same check_stock tool, same gpt-4o-mini - only the SDK changes.
# Run inside .venv_sk (separate venv: semantic-kernel pins its own openai/
# pydantic versions, independent from the AutoGen and MAF demos).
#
# Where AutoGen's "tool" is an MCP server function and MAF's is an
# MCPStdioTool, Semantic Kernel's native unit is a PLUGIN: a class whose
# methods are tagged @kernel_function and registered on a Kernel. This
# plugin model - plus SK's planners for picking which function to call -
# is what MAF's "tools" and built-in function-calling carried forward
# from Semantic Kernel, the same way MAF's workflow graphs carried forward
# AutoGen's multi-agent orchestration ideas.
import asyncio

from dotenv import load_dotenv

load_dotenv()  # reads OPENAI_API_KEY from the .env file

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import kernel_function


# Step 1: a plugin - a plain class, methods tagged @kernel_function become
# callable tools. The docstring/description is what the LLM reads to decide
# whether and how to call it (same idea as an MCP tool's docstring).
class ShopPlugin:
    STOCK = {"laptop": 5, "phone": 0, "headphones": 12}

    @kernel_function(description="Check how many units of a product are in stock.")
    def check_stock(self, product: str) -> str:
        qty = self.STOCK.get(product.lower().rstrip("s"))  # "laptops" -> "laptop"
        if qty is None:
            return f"{product} is not sold in our shop."
        return f"{product}: {qty} units in stock."


async def main():
    # Step 2: the Kernel is SK's central object - it holds the AI service
    # (the "brain") and the plugins (the "tools") together, unlike AutoGen/
    # MAF where the model client and tools are passed straight to the agent.
    kernel = Kernel()
    chat_service = OpenAIChatCompletion(ai_model_id="gpt-4o-mini")
    kernel.add_service(chat_service)
    kernel.add_plugin(ShopPlugin(), plugin_name="Shop")

    # Step 3: FunctionChoiceBehavior.Auto() = "let the model decide, on its
    # own, whether to call a plugin function" - the SK ancestor of AutoGen's
    # reflect_on_tool_use and MAF's automatic tool-calling.
    settings = kernel.get_prompt_execution_settings_from_service_id(chat_service.service_id)
    settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    history = ChatHistory()
    history.add_system_message("You are a shop assistant. Our shop sells: laptop, phone, headphones.")
    history.add_user_message("Do you have laptops in stock?")

    result = await chat_service.get_chat_message_content(chat_history=history, settings=settings, kernel=kernel)
    print("Run 1:", result)

    # Step 4: a second question, same kernel/history - SK keeps the running
    # ChatHistory explicit in your code, instead of hiding it inside an
    # agent object the way AssistantAgent/Agent do.
    history.add_assistant_message(str(result))
    history.add_user_message("And what about phones?")
    result2 = await chat_service.get_chat_message_content(chat_history=history, settings=settings, kernel=kernel)
    print("Run 2:", result2)


asyncio.run(main())
