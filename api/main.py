from fastapi import FastAPI, Body, HTTPException
from .schema import (
    ImageAnalyzeRequest, InventoryChange, RecipeSuggestRequest,
    PlanProfile, NutritionEstimateRequest, NutritionAnalysisRequest
)
from api.planner import router as planner_router
from agents.nutrition_agent import analyze_nutrition_report
from core.models import NutritionAnalysisReport

app = FastAPI(title="AI Nutritionist Agent API", version="0.1.0")

app.include_router(planner_router, prefix="/plan", tags=["plan"])

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

@app.post("/nutrition/estimate")
def estimate_nutrition(payload: NutritionEstimateRequest):
    """
    Output: {"kcal": float, "protein": float, "carbs": float, "fat": float}
    """
    return {"detail": "implement in feat/*"}

@app.post("/nutrition/analyze", response_model=NutritionAnalysisReport, tags=["nutrition"])
def analyze_nutrition(request: NutritionAnalysisRequest = Body(...)):
    """
    식단표 또는 음식 기록을 바탕으로 영양 분석 리포트를 생성합니다.
    """
    # meal_plan과 food_log 중 하나는 반드시 제공되어야 함
    if not request.meal_plan and not request.food_log:
        raise HTTPException(status_code=400, detail="meal_plan 또는 food_log 중 하나는 반드시 제공되어야 합니다.")

    # LLM에 전달할 입력 데이터 준비
    input_data = {}
    if request.meal_plan:
        input_data["meal_plan"] = request.meal_plan.dict()
    if request.food_log:
        input_data["food_log"] = request.food_log

    report = analyze_nutrition_report(input_data)
    return report