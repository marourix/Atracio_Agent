import json
import logging
import warnings
import re
from langchain.agents import initialize_agent, AgentType, Tool
from langchain_community.llms import Ollama

# Supprime les avertissements de LangChain et Ollama
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*LangChain.*")
warnings.filterwarnings("ignore", message=".*Ollama.*")

# Configuration du logging pour afficher les messages d'erreur et d'information
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AtracioAgent")


try:
    with open("data.json", "r", encoding="utf-8") as f:
        mock_data = json.load(f)
    logger.info("Data loaded successfully from data.json")
except FileNotFoundError:
    logger.error("data.json file not found.")
    exit(1)
except json.JSONDecodeError:
    logger.error("JSON format error in data.json")
    exit(1)


def check_stock_level(input_text: str):
    sku = input_text.strip().replace('"', '').replace("'", "")
    if sku.startswith("sku="):
        sku = sku[4:]
    item = mock_data["stock"].get(sku)
    if item:
        available = item['available_qty']
        reserved = item['reserved_qty']
        location = item['location']
        return f" {sku}: {available} units available, {reserved} units reserved at {location}"
    return f" SKU {sku} not found in stock."


def create_purchase_order(input_text: str):
    input_text = input_text.strip().replace('"', '').replace("'", "")
    sku_match = re.search(r'(\w+)', input_text)
    quantity_match = re.search(r'(\d+)', input_text)
    
    if sku_match and quantity_match:
        sku = sku_match.group(1)
        quantity = int(quantity_match.group(1))
        return f"Purchase order created for {quantity} units of {sku}."
    else:
        return "Please provide SKU and quantity (e.g., SKU123 50)"

def check_order_status(input_text: str):
    order_id = input_text.strip().replace('"', '').replace("'", "")
    if order_id.startswith("order_id="):
        order_id = order_id[9:]
    order = mock_data["orders"].get(order_id)
    if order:
        return f"Order {order_id} → Status: {order['status']}, Expected delivery: {order['eta']}."
    return f" Order {order_id} not found."

# ininitialiser le modéle llama3.2
llm = Ollama(model="llama3.2")

# Configurations des outils 
tools = [
    Tool(
        name="check_stock_level",
        func=check_stock_level,
        description="Check stock level for a given SKU. Use this when asked about stock, inventory, or available quantity. Input: SKU code (e.g., SKU123). Returns exact stock data from database."
    ),
    Tool(
        name="create_purchase_order",
        func=create_purchase_order,
        description="Create a purchase order for a given SKU and quantity. Use this when asked to create, buy, or order items. Input: SKU and quantity (e.g., SKU123 50). Returns confirmation message."
    ),
    Tool(
        name="check_order_status",
        func=check_order_status,
        description="Check the status of an order. Use this when asked about order status, delivery, or shipping information. Input: Order ID (e.g., ORD001). Returns exact order data from database."
    )
]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=3,
    return_intermediate_steps=False
)

if __name__ == "__main__":
    print(" Atracio Assistant — Type 'exit' to quit")
    print("Available data:", list(mock_data["stock"].keys()), "|", list(mock_data["orders"].keys()))
    print()
    
    while True:
        try:
            user_input = input(">> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            try:
                response = agent.invoke({"input": user_input})
                print(response["output"])
            except Exception as agent_error:
                logger.error("Agent error: %s", str(agent_error))
                print("Agent processing error. Please try again.")
            
            print()
                
        except KeyboardInterrupt:
            print("\n Goodbye!")
            break
        except Exception as e:
            logger.error("An error occurred: %s", str(e))
            print("An error occurred. Please try again.")
