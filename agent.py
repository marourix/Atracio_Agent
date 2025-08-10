import json
import logging
import warnings
import re
import asyncio
from agents import function_tool
from typing import Optional
from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI
from agents import set_tracing_disabled
import uuid
from datetime import datetime


logging.getLogger("httpx").setLevel(logging.WARNING)

set_tracing_disabled(True)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AtracioAgent")
try:
    with open("data.json", "r", encoding="utf-8") as f:
        mock_data = json.load(f)
    logger.info("Data loaded successfully from data.json")
except FileNotFoundError:
    logger.error(" data.json file not found.")
    exit(1)
except json.JSONDecodeError:
    logger.error(" JSON format error in data.json")
    exit(1)

@function_tool
def check_stock_level(sku: str) -> str:
    """Check stock level for a given SKU."""
    sku = sku.strip().replace('"', '').replace("'", "")
    if sku.startswith("sku="):
        sku = sku[4:]
    item = mock_data["stock"].get(sku)
    if item:
        return f"{sku}: {item['available_qty']} units available, {item['reserved_qty']} units reserved at {item['location']}."
    return f"SKU {sku} not found in stock."

@function_tool

def create_purchase_order(input_text: str):
    input_text = input_text.strip().replace('"', '').replace("'", "")
    sku_match = re.search(r'(SKU\d+)', input_text, re.IGNORECASE)
    quantity_match = re.search(r'\b(?!\d+$)(\d+)\b', input_text)
    
    if not (sku_match and quantity_match):
        return "Please provide both a valid SKU and a quantity (e.g., 'Create a purchase order for SKU123 50')."
    
    sku = sku_match.group(1).upper()
    quantity = int(quantity_match.group(1))
    
    # Vérification si le produit existe dans le stock
    if sku not in mock_data["stock"]:
        return f"The SKU '{sku}' does not exist in the current stock database."
    
    order_id = f"PO{uuid.uuid4().hex[:6].upper()}"
    
    order_data = {
        "sku": sku,
        "quantity": quantity,
        "status": "Pending",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if "purchase_orders" not in mock_data:
        mock_data["purchase_orders"] = {}
    
    mock_data["purchase_orders"][order_id] = order_data
   
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(mock_data, f, indent=4)
    
    return (
        f"Purchase order {order_id} has been successfully created.\n"
        f"SKU: {sku}, Quantity: {quantity} units, Status: {order_data['status']}."
    )
@function_tool
def check_order_status(order_id: str) -> str:
    """Check the status of an order."""
    order_id = order_id.strip().replace('"', '').replace("'", "")
    if order_id.startswith("order_id="):
        order_id = order_id[9:]
    order = mock_data["orders"].get(order_id)
    if order:
        return f"Order {order_id} → Status: {order['status']}, Expected delivery: {order['eta']}."
    return f"Order {order_id} not found."


model = OpenAIChatCompletionsModel(
    model="llama3.2",
    openai_client=AsyncOpenAI(
        base_url="http://localhost:11434/v1",
        api_key="nokeyneeded"
    )
)


AGENT_INSTRUCTIONS = """
You are Atracio's ERP assistant. 
You must answer business-related questions using ONLY the provided tools.
When creating a purchase order, ALWAYS call the `create_purchase_order` tool and return ONLY the tool's result to the user in natural language.


TOOLS:
1. check_stock_level(sku: str)
2. create_purchase_order(sku: str, quantity: int)
3. check_order_status(order_id: str)

RULES:
- Always use the tools to answer questions.
- Do NOT invent data, only use the loaded mock data.
- Be concise and professional.
"""

agent = Agent(
    name="Atracio Assistant",
    instructions=AGENT_INSTRUCTIONS,
    tools=[check_stock_level, create_purchase_order, check_order_status],
    model=model
)

async def stream_response(user_input: str):
    try:
        result = Runner.run_streamed(agent, user_input)
        async for event in result.stream_events():
            if event.type == "raw_response_event" and hasattr(event.data, 'delta'):
                content = event.data.delta
                if content.strip() and not content.startswith("{"):
                    print(content, end="", flush=True)
        print()
    except Exception as e:
        logger.error(f" Error: {str(e)}")

async def main():
    print("Atracio Assistant — Type 'exit' to quit")
    print("Available data:", list(mock_data["stock"].keys()), "|", list(mock_data["orders"].keys()))
    print()

    while True:
        user_input = input(">> ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Goodbye!")
            break
        await stream_response(user_input)

if __name__ == "__main__":
    asyncio.run(main())
