# 파일 위치: api/main.py

import base64
from typing import Annotated, Optional
import json

from fastapi import FastAPI, File, Form, HTTPException

# --- LangGraph 워크플로우와 필요한 에이전트를 가져옵니다 ---
from core.graph_builder import app as agent_workflow
from agents.inventory_agent import InventoryAgent

# --- FastAPI 앱 초기화 ---
app = FastAPI(title="AI 영양사 에이전트 API", version="0.1.0")


# --- API 엔드포인트(기능 목록) 정의 ---

# ✨ 워크플로우를 직접 호출하는 새로운 통합 엔드포인트 ✨
@app.post("/analyze-and-suggest", tags=["핵심 기능"])
async def analyze_and_suggest(
    file: Annotated[bytes, File()],
    constraints: Optional[str] = Form(default="{}") # JSON 문자열로 제약조건 받기
):
    """
    냉장고 이미지를 받아 재고 분석부터 레시피 추천까지
    전체 AI 에이전트 워크플로우를 실행합니다.
    """
    try:
        # JSON 문자열을 딕셔너리로 변환
        constraints_dict = json.loads(constraints)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="'constraints'가 유효한 JSON 형식이 아닙니다.")

    image_base64 = base64.b64encode(file).decode("utf-8")
    
    # LangGraph 워크플로우 실행
    initial_state = {
        "image_base64": image_base64,
        "constraints": constraints_dict
    }
    final_state = agent_workflow.invoke(initial_state)
    
    # 최종 결과에서 필요한 정보만 추출하여 반환
    return {
        "inventory": final_state.get("inventory", {}),
        "recipes": final_state.get("recipes", [])
    }


# --- 이하 엔드포인트는 보조 기능 또는 미구현 기능입니다 ---
@app.get("/inventory", tags=["보조 기능"])
def read_inventory():
    """현재 저장된 재고 목록을 보여줍니다."""
    inventory_agent = InventoryAgent()
    current_inventory = inventory_agent.load_inventory()
    return {"items": current_inventory}

# (다른 미구현 엔드포인트들은 그대로 유지됩니다)
# ...