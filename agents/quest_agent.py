"""
Quest Agent - LLM 기반 일일 퀘스트 생성

사용자의 레시피, 식단 목표, 재고 상황에 맞춰 개인화된 일일 퀘스트를 생성합니다.
퀘스트 완료 시 XP를 획득하여 게임화 요소를 제공합니다.
"""

from typing import List, Dict, Any, Optional
import os
import json
import logging
from datetime import date
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("quest_agent")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)


def generate_daily_quests(
    recipes: List[Dict[str, Any]],
    inventory: Dict[str, Any],
    constraints: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    사용자의 레시피, 재고, 제약 조건을 기반으로 일일 퀘스트를 생성합니다.

    Args:
        recipes: 추천된 레시피 목록
        inventory: 현재 재고 상태
        constraints: 사용자 제약 조건 (식단 목표 등)

    Returns:
        퀘스트 목록 [{"id": str, "title": str, "reason": str, "xp": int, "checks": list}]
    """
    try:
        from openai import OpenAI
    except ImportError:
        logger.error("openai library not found. pip install openai")
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; Quest generation skipped.")
        return []

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # 퀘스트 생성을 위한 컨텍스트 구성
    recipe_titles = [r.get("title", "알 수 없음") for r in recipes[:3]]
    inventory_items = list(inventory.keys()) if inventory else []
    dietary_goals = constraints.get("dietary_goals", "균형 잡힌 식단")

    system_prompt = """당신은 사용자의 건강과 영양 목표를 달성하도록 돕는 AI 영양 코치입니다.
사용자의 상황에 맞는 실용적이고 재미있는 일일 퀘스트를 생성해주세요.

퀘스트는 다음 원칙을 따라야 합니다:
1. 실제로 달성 가능하고 구체적이어야 합니다
2. 사용자의 식단 목표와 연결되어야 합니다
3. 추천된 레시피나 현재 재고를 활용하도록 유도해야 합니다
4. 재미있고 동기 부여가 되는 톤으로 작성되어야 합니다

응답은 반드시 JSON 형식으로만 제공하세요."""

    user_message = f"""오늘의 상황:
- 추천 레시피: {', '.join(recipe_titles)}
- 냉장고 재료: {', '.join(inventory_items[:10])}
- 식단 목표: {dietary_goals}

위 정보를 바탕으로 3개의 일일 퀘스트를 생성해주세요.
각 퀘스트는 다음 JSON 형식이어야 합니다:
{{
  "quests": [
    {{
      "id": "unique_id",
      "title": "퀘스트 제목 (30자 이내)",
      "reason": "이 퀘스트를 해야 하는 이유 (50자 이내)",
      "xp": 획득 XP (10~50 사이),
      "checks": ["체크리스트1", "체크리스트2"]
    }}
  ]
}}

예시:
{{
  "quests": [
    {{
      "id": "cook_recipe_1",
      "title": "오늘의 추천 레시피 한 가지 요리하기",
      "reason": "냉장고 재료를 활용하면 음식물 쓰레기를 줄일 수 있어요",
      "xp": 30,
      "checks": ["레시피 선택", "재료 준비", "요리 완성"]
    }},
    {{
      "id": "protein_goal",
      "title": "단백질 30g 이상 섭취하기",
      "reason": "근육 건강과 포만감 유지에 도움이 됩니다",
      "xp": 20,
      "checks": ["아침 단백질", "점심 단백질", "저녁 단백질"]
    }},
    {{
      "id": "vegetable_variety",
      "title": "3가지 이상의 채소 섭취하기",
      "reason": "다양한 영양소와 식이섬유를 섭취할 수 있습니다",
      "xp": 25,
      "checks": ["채소1", "채소2", "채소3"]
    }}
  ]
}}

JSON 외의 텍스트는 절대 포함하지 마세요."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        quests = data.get("quests", [])

        # ID 중복 방지를 위해 날짜 접두사 추가
        today = date.today().strftime("%Y%m%d")
        for i, quest in enumerate(quests):
            quest["id"] = f"{today}_{quest.get('id', f'quest_{i}')}"

        logger.info(f"퀘스트 생성 완료: {len(quests)}개")
        return quests

    except json.JSONDecodeError as e:
        logger.error(f"퀘스트 JSON 파싱 실패: {e}")
        return []
    except Exception as e:
        logger.error(f"퀘스트 생성 실패: {e}")
        return []


# CLI 테스트
if __name__ == "__main__":
    test_recipes = [
        {"title": "김치볶음밥"},
        {"title": "된장찌개"},
        {"title": "계란말이"}
    ]
    test_inventory = {"김치": {}, "계란": {}, "양파": {}, "두부": {}}
    test_constraints = {"dietary_goals": "저염식"}

    quests = generate_daily_quests(test_recipes, test_inventory, test_constraints)
    print(json.dumps(quests, indent=2, ensure_ascii=False))
