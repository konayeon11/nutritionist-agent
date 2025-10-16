from fastapi import FastAPI
from .schema import (
    ImageAnalyzeRequest, InventoryChange, RecipeSuggestRequest,
    PlanProfile, NutritionEstimateRequest
)

app = FastAPI(title="AI Nutritionist Agent API", version="0.1.0")

@app.get("/health")
def health():
    return {"status": "ok"}

# 이하 엔드포인트는 시그니처만 노출 (feat/*에서 구현)
@app.post("/vision/analyze")
def analyze_image(payload: ImageAnalyzeRequest):
    """
    Input: ImageAnalyzeRequest(image_b64)
    Output: [{"name": str, "confidence": float}, ...]
    """
    return {"detail": "implement in feat/*"}

@app.get("/inventory")
def read_inventory():
    """
    Output: {"items":[{"name": str, "quantity": float, "unit": str}, ...]}
    """
    return {"detail": "implement in feat/*"}

@app.post("/inventory/update")
def update_inventory(changes: list[InventoryChange]):
    """
    Input: list of InventoryChange
    Output: {"ok": bool}
    """
    return {"detail": "implement in feat/*"}

@app.post("/recipes/suggest")
def suggest_recipes(payload: RecipeSuggestRequest):
    """
    Output:
      [{"title": str, "ingredients": List[str], "steps": List[str]}, ...]
    """
    return {"detail": "implement in feat/*"}

@app.post("/plan/weekly")
def plan_week(payload: PlanProfile):
    """
    Output: {"week": [{"day": "Mon", "meals": [...]}, ...]}
    """
    return {"detail": "implement in feat/*"}

@app.post("/nutrition/estimate")
def estimate_nutrition(payload: NutritionEstimateRequest):
    """
    Output: {"kcal": float, "protein": float, "carbs": float, "fat": float}
    """
    return {"detail": "implement in feat/*"}
