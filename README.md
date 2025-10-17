# ai-nutritionist-agent (skeleton)

협업용 기본 뼈대만 포함합니다. 구현 코드는 각자 feat/* 브랜치에서 진행 후 PR로 dev에 병합합니다.

## 구조
```plaintext
📦 ai-nutritionist-agent
│
├── agents/                     # 각 기능별 AI Agent 모듈
│   ├── __init__.py
│   ├── vision_agent.py         # 냉장고 이미지 분석
│   ├── online_order_agent      # 온라인 주문 데이터를 처리
│   ├── inventory_agent.py      # 재고·유통기한 관리
│   ├── recipe_agent.py         # 맞춤형 레시피 추천
│   ├── planner_agent.py        # 주간 식단·쇼핑리스트 생성
│   └── nutrition_agent.py      # 영양분 분석 및 피드백
│
├── core/                       # LangGraph / Memory / Utils 등 핵심 로직
│   ├── __init__.py
│   ├── graph_builder.py        # 멀티에이전트 플로우 정의
│   ├── memory_manager.py       # 세션·장기 기억 관리
│   └── utils.py                # 공용 유틸 함수
│
├── api/                        # FastAPI 기반 서버 엔트리포인트
│   ├── __init__.py
│   ├── main.py                 # FastAPI 엔트리 포인트
│   └── schema.py               # Pydantic 데이터 모델 정의
│
├── data/                       # 샘플 데이터 / 리소스
│   └── sample_inventory.json
│
├── tests/                      # 단위 테스트 코드
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_memory.py
│
├── README.md                   # 프로젝트 개요 및 실행 가이드
├── requirements.txt             # 패키지 의존성 목록
└── .gitignore                   # 캐시·환경파일 제외 설정
```


## 빠른 실행 (개발용)
pip install -r requirements.txt
uvicorn api.main:app --reload

## 브랜치 전략
- main: 배포/안정
- dev: 통합 개발
- feat/*: 개인 기능 브랜치 → PR → dev

개요 (RecipeAgent)

목적: 냉장고 인벤토리 + 사용자 제약을 받아, 웹 신뢰 출처(가능하면) 또는 합성(synthetic)으로 한국어 레시피 Top N을 생성.

핵심 기능:

알레르기/기피 식품 필터

인벤토리 교집합(uses)과 누락(missing) 계산 (물/기본양념은 자동 제외)

시간/식단 목표 반영(예: 저염)

신뢰 출처 URL이 있으면 포함, 없으면 source.name="synthetic"

고객 카드 문구(마케팅 톤) 자동 생성 — ‘왜 추천했는지’가 한 줄로 요약됨

입력 데이터(Inputs)

agents/recipe_agent.py:suggest_recipes(ingredients, constraints)

ingredients: List[str]
예) ["계란", "양파", "대파"]
※ “물/소금/간장/후추/식용유/된장/고추장/다시다…” 등은 STOPWORDS로 등록되어 누락에서 제외됨.

constraints: Dict[str, Any]

openai_api_key: str (필수/권장)

target_count: int (기본 3) — 추천 개수

max_missing: int (기본 3) — 허용 가능한 누락 재료 개수

diet: str | None (예: "low_sodium")

time_max: int | None (분 단위 최대 조리시간)

(선택) allergies: List[str], dislikes: List[str], preferred_cuisines: List[str], health_context: Dict

샘플 CLI:

python agents/recipe_agent.py --debug --target_count 3 --max_missing 2

출력 데이터(Outputs)

suggest_recipes(...) -> List[Dict[str, Any]]
프론트가 그대로 파싱해 쓰도록 최종 결과만 반환.

레코드 스키마(프론트 계약)
{
  "id": "string",                        // 안정적 해시 ID
  "title": "string",                     // 한국어 레시피명
  "ingredients": ["..."],                // 레시피 재료 원문
  "steps": ["..."],                      // 단계별 조리법(한국어)
  "time_minutes": 20,                    // 총 소요시간(분) - 있을 때만
  "time_breakdown": {"prep":5,"cook":15,"total":20},  // 부분 시간 - 있을 때만
  "servings": 2,                         // 인분 - 있을 때만
  "difficulty": "쉬움",                  // 있을 때만
  "tags": ["한식","간단"],              // 있을 때만

  "source": {                            // 신뢰 출처(있으면)
    "name": "한국 요리 블로그",
    "url": "https://..."
  },

  "nutrition": {                         // 1인분 기준(있으면)
    "calories_kcal": 300,
    "protein_g": 12.0,
    "carbs_g": 40.0,
    "fat_g": 10.0,
    "sodium_mg": 200
  },

  "uses": ["계란","양파"],               // 인벤토리와 겹친 재료
  "missing": ["밥"],                      // 인벤토리에 없는 핵심 재료(기본양념 제외)
  "suitability": {                        // 적합성 설명(있으면)
    "summary": "빠르고 간단한 한끼",
    "health": "저염 조리로 나트륨 부담↓",   // 모델이 보낼 수 있음(출력에서는 '추천 이유'로 렌더 권장)
    "inventory": "계란·양파 활용",
    "time": "20분 이내",
    "occasion": "일상식/간단 반찬",
    "skill": "초보자 가능",
    "tips": ["팬 예열 충분히", "양파는 충분히 볶아 단맛↑"],
    "warnings": ["알레르기 주의: 난류"]
  },

  "storage": "냉장 1~2일 권장",          // 있을 때만
  "customer_card": "멀티라인 한국어 요약 텍스트"  // UI용 카피 문구(한 줄 요약+요점)
}
