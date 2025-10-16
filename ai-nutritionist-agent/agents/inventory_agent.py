"""
InventoryAgent: 재고 관리/조회 (인터페이스만)
"""
from typing import List, Dict, Any

def get_inventory() -> Dict[str, Any]:
    """
    Output: {"items":[{"name": str, "quantity": float, "unit": str}, ...]}
    """
    raise NotImplementedError

def update_inventory(changes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Input: [{"name": str, "delta": float, "unit": str}, ...]
    Output: {"ok": bool}
    """
    raise NotImplementedError
