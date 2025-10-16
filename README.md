# ai-nutritionist-agent (skeleton)

협업용 기본 뼈대만 포함합니다. 구현 코드는 각자 feat/* 브랜치에서 진행 후 PR로 dev에 병합합니다.

## 구조
📦 ai-nutritionist-agent
│
├── agents/                          # 각 기능별 AI Agent 모듈
│   ├── __init__.py
│   ├── vision_agent.py              # 냉장고/영수증 이미지 분석
│   ├── inventory_agent.py           # 재고·유통기한 관리
│   ├── recipe_agent.py              # 맞춤형 레시피 추천
│   ├── planner_agent.py             # 주간 식단·쇼핑리스트 생성
│   └── nutrition_agent.py           # 영양분 분석 및 피드백
│
├── core/                            # LangGraph / Memory / Utils 등 핵심 로직
│   ├── __init__.py
│   ├── graph_builder.py             # 멀티에이전트 플로우 정의
│   ├── memory_manager.py            # 세션·장기 기억 관리
│   └── utils.py                     # 공용 유틸 함수
│
├── api/                             # FastAPI 기반 서버 엔드포인트
│   ├── __init__.py
│   ├── main.py                      # FastAPI 엔트리 포인트
│   └── schema.py                    # Pydantic 데이터 모델 정의
│
├── data/                            # 샘플 데이터 / 리소스
│   └── sample_inventory.json
│
├── tests/                           # 단위 테스트 코드
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_memory.py
│
├── README.md                        # 프로젝트 개요 및 실행 가이드
├── requirements.txt                 # 패키지 의존성 목록
└── .gitignore                       # 캐시·환경파일 제외 설정



## 빠른 실행 (개발용)
pip install -r requirements.txt
uvicorn api.main:app --reload

## 브랜치 전략
- main: 배포/안정
- dev: 통합 개발
- feat/*: 개인 기능 브랜치 → PR → dev
