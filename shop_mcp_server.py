# A tiny MCP server: it exposes our shop's tools to ANY agent.
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ShopServer")

STOCK = {"laptop": 5, "phone": 0, "headphones": 12}


@mcp.tool()
def check_stock(product: str) -> str:
    """Check how many units of a product are in stock."""
    qty = STOCK.get(product.lower().rstrip("s"))  # "laptops" -> "laptop"
    if qty is None:
        return f"{product} is not sold in our shop."
    return f"{product}: {qty} units in stock."


if __name__ == "__main__":
    mcp.run()  # talks over stdio
