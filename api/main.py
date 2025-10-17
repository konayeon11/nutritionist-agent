import base64
from typing import Annotated

from fastapi import FastAPI, Body, HTTPException, File

# --- 필요한 모든 에이전트와 모델들을 가져옵니다 ---
from core.graph_builder import app as graph_app
from agents.recipe_agent import suggest_recipes as suggest_recipes_from_agent
from agents.inventory_agent import InventoryAgent
from agents.nutrition_agent import analyze_nutrition_report
from core.models import NutritionAnalysisReport
from api.planner import router as planner_router
from .schema import (
    InventoryChange, RecipeSuggestRequest,
    NutritionEstimateRequest, NutritionAnalysisRequest
)

# --- FastAPI 앱 초기화 ---
app = FastAPI(title="AI 영양사 에이전트 API", version="0.1.0")

# 다른 파일(planner.py)에 정의된 API들을 포함시킵니다.
app.include_router(planner_router, prefix="/plan", tags=["plan"])


# --- API 엔드포인트(기능 목록) 정의 ---

@app.get("/health", tags=["기본"])
def health():
    """서버가 정상적으로 작동하는지 확인합니다."""
    return {"status": "ok"}

@app.post("/vision/analyze", tags=["기능"])
async def analyze_image(file: Annotated[bytes, File()]):
    """
    냉장고 이미지를 받아 AI 에이전트 워크플로우를 실행하고,
    업데이트된 재고 목록을 반환합니다.
    """
    image_base64 = base64.b64encode(file).decode("utf-8")
    initial_state = {"image_base64": image_base64}
    final_state = graph_app.invoke(initial_state)
    return {"inventory": final_state.get("inventory", {})}

@app.get("/inventory", tags=["기능"])
def read_inventory():
    """
    현재 저장된 재고 목록(inventory.json)을 불러와 보여줍니다.
    """
    inventory_agent = InventoryAgent()
    current_inventory = inventory_agent.load_inventory()
    return {"items": current_inventory}

@app.post("/inventory/update", tags=["기능"])
def update_inventory(changes: list[InventoryChange]):
    """
    재고를 수동으로 업데이트합니다.
    """
    return {"detail": "아직 구현되지 않은 기능입니다."}

@app.post("/recipes/suggest", tags=["기능"])
def suggest_recipes(payload: RecipeSuggestRequest):
    """
    현재 재고를 바탕으로 레시피를 추천합니다.
    """
    constraints_dict = payload.constraints if payload.constraints else {}
    recipes = suggest_recipes_from_agent(
        ingredients=payload.ingredients,
        constraints=constraints_dict
    )
    return recipes

@app.post("/nutrition/estimate", tags=["기능"])
def estimate_nutrition(payload: NutritionEstimateRequest):
    """
    음식의 영양 정보를 추정합니다.
    """
    return {"detail": "아직 구현되지 않은 기능입니다."}

@app.post("/nutrition/analyze", response_model=NutritionAnalysisReport, tags=["nutrition"])
def analyze_nutrition(request: NutritionAnalysisRequest = Body(...)):
    """
    식단표 또는 음식 기록을 바탕으로 영양 분석 리포트를 생성합니다.
    """
    if not request.meal_plan and not request.food_log:
        raise HTTPException(status_code=400, detail="meal_plan 또는 food_log 중 하나는 반드시 제공되어야 합니다.")

    input_data = {}
    if request.meal_plan:
        input_data["meal_plan"] = request.meal_plan.model_dump()
    if request.food_log:
        # --- ✨ 핵심 수정 부분 ✨ ---
        # '.model_dump()'를 제거했습니다. 
        # request.food_log는 이미 딕셔너리 리스트이므로 변환이 필요 없습니다.
        input_data["food_log"] = request.food_log

    # 실제 NutritionAgent의 함수를 호출합니다.
    report = analyze_nutrition_report(input_data)
    return report

