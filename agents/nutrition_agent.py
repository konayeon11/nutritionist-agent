"""
NutritionAgent: 레시피/식단의 대략적 영양소 추정 (인터페이스만)
"""
from typing import Dict, Any

def estimate_nutrition(recipe: Dict[str, Any]) -> Dict[str, float]:
    """
    Input: recipe payload (title/ingredients/amounts)
    Output: {"kcal": float, "protein": float, "carbs": float, "fat": float}
    """
    raise NotImplementedError
