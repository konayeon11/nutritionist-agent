from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ImageAnalyzeRequest(BaseModel):
    image_b64: str  # base64

class InventoryChange(BaseModel):
    name: str
    delta: float
    unit: str

class RecipeSuggestRequest(BaseModel):
    ingredients: List[str]
    constraints: Optional[Dict[str, Any]] = None

class PlanProfile(BaseModel):
    age: int
    sex: str  # "M" or "F"
    goal: str # "cut"|"bulk"|"maintain"

class NutritionEstimateRequest(BaseModel):
    recipe: Dict[str, Any]
