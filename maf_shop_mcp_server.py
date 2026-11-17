# The same shop tool as shop_mcp_server.py, exposed through mcp>=2.x's MCPServer
# (the AutoGen demo pins mcp==1.19.0, where this class is still called FastMCP;
# this file lets the MAF demo run against a newer mcp in its own .venv_maf).
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("ShopServer")

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
