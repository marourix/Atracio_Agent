# Atracio_Agent
This agent is used with fictive data to simulate basic ERP operations for Atracio, including stock checks, order creation, and sales tracking. It leverages the OPEN AI Agent Sdk with a local LLM via Ollama.


##  Features

-  Check stock levels (`stock.consulter_niveau`)
-  Create purchase orders (`achats.creer_commande`)
-  Get sales order status (`ventes.statut_commande`)
-  Powered by LLaMA 3.2 (Ollama)
-  Natural language queries

##  Tools Implemented

| Tool Name             | Description                                      |
|-----------------------|--------------------------------------------------|
| `check_stock_level`   | Returns available and reserved quantity of SKU   |
| `create_purchase_order` | Simulates creation of a purchase order         |
| `check_order_status`  | Returns the status and ETA of a given order      |

##  Mock Data

Mock data is loaded from a local file `data.json`. This allows the agent to respond without accessing real databases.

Example:

```json
{
  "stock": {
    "SKU123": {
      "available_qty": 150,
      "reserved_qty": 20,
      "location": "Warehouse A"
    }
  },
  "orders": {
    "ORD001": {
      "status": "Shipped",
      "eta": "2025-08-01"
    }
  }
}


