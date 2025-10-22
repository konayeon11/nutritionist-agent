# 파일 위치: api/main.py

import base64
from typing import Annotated, Optional
import json

from fastapi import FastAPI, File, Form, HTTPException
from starlette.middleware.cors import CORSMiddleware # CORS 미들웨어 임포트
from pydantic import BaseModel # Pydantic BaseModel 임포트

# --- LangGraph 워크플로우와 필요한 에이전트를 가져옵니다 ---
from core.graph_builder import app as agent_workflow, image_app # image_app 임포트
from agents.inventory_agent import InventoryAgent
from core.database import DatabaseManager

# --- FastAPI 앱 초기화 ---
app = FastAPI(title="AI 영양사 에이전트 API", version="0.1.0")

# --- Pydantic 모델 정의 ---
class ChatMessage(BaseModel):
    message: str
    constraints: Optional[dict] = {}

# --- CORS 설정 ---
origins = [
    "http://localhost:5173",  # Vue.js 개발 서버 기본 포트
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # Vue.js 개발 서버 대체 포트
    "http://127.0.0.1:5174",
    "http://localhost:3000",  # Docker 프론트엔드 포트
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- API 엔드포인트(기능 목록) 정의 ---

# 헬스 체크 엔드포인트
@app.get("/health", tags=["시스템"])
async def health_check():
    """서버 상태를 확인합니다."""
    return {"status": "ok", "message": "서버가 정상적으로 동작 중입니다."}

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
    
    # LangGraph 워크플로우 실행 (vision_node부터 시작)
    initial_state = {
        "image_base64": image_base64,
        "constraints": constraints_dict
    }
    # image_app을 호출하도록 변경
    final_state = image_app.invoke(initial_state, config={"configurable": {"thread_id": "image_analysis_thread"}})
    
    # recognized_inventory를 new_items로부터 생성
    recognized_inventory = {item.get("item_name"): {"quantity": item.get("quantity", 1)} for item in final_state.get("new_items", []) if item.get("item_name")}

    # 최종 결과에서 필요한 정보만 추출하여 반환
    return {
        "inventory": recognized_inventory,
        "recipes": final_state.get("recipes", []),
        "shopping_list": final_state.get("shopping_list"),
        "quests": final_state.get("quests", [])
    }

@app.post("/chat", tags=["챗봇"])
async def chat_with_agent(chat_request: ChatMessage):
    """
    챗봇 형식으로 AI 에이전트와 대화합니다.
    사용자 메시지를 받아 적절한 응답을 반환합니다.
    """
    initial_state = {
        "chat_message": chat_request.message,
        "constraints": chat_request.constraints or {}
    }
    final_state = agent_workflow.invoke(initial_state)
    
    response_data = {
        "response": final_state.get("response", "요청을 처리할 수 없습니다.")
    }

    # 'get_recipes' 의도일 경우, 레시피와 쇼핑 리스트를 응답에 추가
    if final_state.get("intent", {}).get("intent") == "get_recipes":
        shopping_list_data = final_state.get("shopping_list")
        if shopping_list_data is not None:
            response_data["shopping_list"] = shopping_list_data
        
        recipes_data = final_state.get("recipes")
        if recipes_data is not None:
            response_data["recipes"] = recipes_data

    return response_data


# --- 이하 엔드포인트는 보조 기능 또는 미구현 기능입니다 ---
@app.get("/inventory", tags=["보조 기능"])
def read_inventory():
    """현재 저장된 재고 목록을 보여줍니다."""
    db_manager = DatabaseManager()
    current_inventory = db_manager.get_inventory()
    return {"items": current_inventory}

# (다른 미구현 엔드포인트들은 그대로 유지됩니다)
# ...