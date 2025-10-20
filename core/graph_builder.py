# 파일 위치: core/graph_builder.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
import base64

# --- 필요한 모든 에이전트와 모델들을 가져옵니다 ---
from agents.vision_agent import VisionAgent
from agents.inventory_agent import InventoryAgent
from agents.recipe_agent import suggest_recipes as suggest_recipes_from_agent
# ✨ 새로 수정한 PlannerAgent 함수를 가져옵니다 ✨
from agents.planner_agent import create_daily_plan_and_shopping_list
from core.models import DailyMealPlan, ShoppingList

# --- 상태 정의 ---
class AgentState(TypedDict):
    image_base64: str
    constraints: Optional[Dict[str, Any]]
    new_items: List[dict]
    inventory: Dict
    ingredients: List[str]
    recipes: List[Dict]
    meal_plan: Optional[DailyMealPlan]
    shopping_list: Optional[ShoppingList]

# --- 에이전트 인스턴스 ---
vision_agent = VisionAgent()
inventory_agent = InventoryAgent()

# --- 그래프 노드 함수 ---
def run_vision_agent(state: AgentState) -> dict:
    print("--- 1. Vision Agent 실행 ---")
    image_base64 = state["image_base64"]
    new_items = vision_agent.analyze_image(image_base64)
    ingredients = [item.get("item_name") for item in new_items if item.get("item_name")]
    return {"new_items": new_items, "ingredients": ingredients}

def run_inventory_agent(state: AgentState) -> dict:
    print("--- 2. Inventory Agent 실행 ---")
    new_items = state["new_items"]
    updated_inventory = inventory_agent.update_inventory(new_items)
    return {"inventory": updated_inventory}

def run_recipe_agent(state: AgentState) -> dict:
    print("--- 3. Recipe Agent 실행 ---")
    ingredients = state["ingredients"]
    constraints = state.get("constraints") or {}
    recipes = suggest_recipes_from_agent(ingredients=ingredients, constraints=constraints)
    return {"recipes": recipes}

# --- ✨ PlannerAgent를 위한 노드 수정 ✨ ---
def run_planner_agent(state: AgentState) -> dict:
    print("--- 4. Planner Agent 실행 ---")
    recipes = state.get("recipes", [])
    inventory = state.get("inventory", {})
    
    if not recipes:
        return {}

    # PlannerAgent 함수를 직접 호출합니다.
    meal_plan, shopping_list = create_daily_plan_and_shopping_list(
        user_selected_recipes=recipes, # 실제 앱에서는 사용자가 선택한 레시피
        current_inventory=inventory
    )
    
    return {"meal_plan": meal_plan, "shopping_list": shopping_list}

# --- 그래프 생성 및 연결 ---
workflow = StateGraph(AgentState)

workflow.add_node("vision_node", run_vision_agent)
workflow.add_node("inventory_node", run_inventory_agent)
workflow.add_node("recipe_node", run_recipe_agent)
workflow.add_node("planner_node", run_planner_agent)

workflow.set_entry_point("vision_node")
workflow.add_edge("vision_node", "inventory_node")
workflow.add_edge("inventory_node", "recipe_node")
workflow.add_edge("recipe_node", "planner_node")
workflow.add_edge("planner_node", END)

app = workflow.compile()
print("LangGraph 워크플로우가 [최신 PlannerAgent]를 포함하여 완성되었습니다.")