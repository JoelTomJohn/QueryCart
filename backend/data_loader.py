import csv
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

_CACHED_ORDERS: Optional[List[Dict[str, Any]]] = None
_CACHED_PATH: Optional[str] = None

def load_orders(csv_path: Optional[str] = None, force_reload: bool = False) -> List[Dict[str, Any]]:
    """
    Load orders from CSV, validate schema, cast types, and cache in-memory.
    Throws FileNotFoundError or ValueError with explicit messages if invalid.
    """
    global _CACHED_ORDERS, _CACHED_PATH
    
    if csv_path is None:
        from backend.config import ORDERS_CSV_PATH
        csv_path = ORDERS_CSV_PATH

    path_obj = Path(csv_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Orders dataset file not found at: {path_obj.resolve()}")

    if not force_reload and _CACHED_ORDERS is not None and _CACHED_PATH == str(path_obj.resolve()):
        return _CACHED_ORDERS

    orders: List[Dict[str, Any]] = []
    required_columns = {
        "order_id", "order_date", "customer_name", "city",
        "product", "category", "quantity", "unit_price_inr",
        "total_inr", "payment_method", "status"
    }

    with open(path_obj, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV file at {csv_path} is empty or missing headers.")
        
        missing = required_columns - set(col.strip() for col in reader.fieldnames)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

        for line_num, row in enumerate(reader, start=2):
            try:
                order_id = str(row["order_id"]).strip().upper()
                order_date = str(row["order_date"]).strip()
                customer_name = str(row["customer_name"]).strip()
                city = str(row["city"]).strip()
                product = str(row["product"]).strip()
                category = str(row["category"]).strip()
                quantity = int(row["quantity"])
                unit_price_inr = float(row["unit_price_inr"])
                total_inr = float(row["total_inr"])
                payment_method = str(row["payment_method"]).strip()
                status = str(row["status"]).strip().lower()

                orders.append({
                    "order_id": order_id,
                    "order_date": order_date,
                    "customer_name": customer_name,
                    "city": city,
                    "product": product,
                    "category": category,
                    "quantity": quantity,
                    "unit_price_inr": unit_price_inr,
                    "total_inr": total_inr,
                    "payment_method": payment_method,
                    "status": status,
                })
            except (ValueError, KeyError) as e:
                raise ValueError(f"Error parsing row {line_num} in {csv_path}: {e}")

    _CACHED_ORDERS = orders
    _CACHED_PATH = str(path_obj.resolve())
    return orders

def get_orders() -> List[Dict[str, Any]]:
    return load_orders()
