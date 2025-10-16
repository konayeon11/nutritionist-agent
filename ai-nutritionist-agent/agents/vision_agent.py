"""
VisionAgent: 이미지 → 식품/영양 성분 후보 추출 (인터페이스만)
"""
from typing import List, Dict, Any

def analyze_food_image(image_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Input: raw image bytes
    Output: [{"name": str, "confidence": float}, ...]
    """
    raise NotImplementedError("Implement in feat/* branch")
