# 미리 (MIRI) - AI 영양사

**Meal & Intelligence for Real-life Integration**

당신의 식탁을 미리 준비하는 AI 영양사 서비스입니다.

---

## 🎯 주요 기능

### 🍳 냉장고 스캔 및 재료 관리
- 냉장고 사진을 업로드하면 AI가 자동으로 재료 인식
- 유통기한 자동 계산 및 관리
- 재료별 적절한 단위 자동 부여 (개, 팩, g, ml 등)

### 💬 AI 챗봇 레시피 추천
- 자연어로 대화하며 레시피 검색
- "감자전 만들고 싶어", "고기 요리 추천해줘" 등 특정 요리명 인식
- 냉장고 재료 기반 맞춤 레시피 제안

### 📋 스마트 레시피 검색
- 만개의레시피 API 연동
- LLM 기반 레시피 생성
- 재료 매칭률 및 영양 정보 표시

### 🎮 퀘스트 & 레벨 시스템
- 일일/주간 퀘스트 완료로 XP 획득
- 레벨업을 통한 게이미피케이션

### 👤 개인화 프로필
- 건강 목표, 식단 선호도 설정
- 로컬 저장으로 개인정보 보호

---

## 🛠️ 기술 스택

### 백엔드
- **LangGraph**: 멀티 에이전트 워크플로우 오케스트레이션
- **LangChain**: LLM 체이닝 및 프롬프트 관리
- **FastAPI**: RESTful API 서버
- **OpenAI GPT-4o**: 이미지 분석, 레시피 생성, 챗봇
- **SQLite**: 로컬 데이터베이스
- **BeautifulSoup4**: 웹 스크래핑

### 프론트엔드
- **Vue 3**: Composition API
- **Vite**: 빌드 도구
- **localStorage**: 클라이언트 데이터 저장

---

## 📁 프로젝트 구조

```
nutritionist-agent/
├── agents/                      # AI 에이전트 모듈
│   ├── chat_agent.py           # 챗봇 인텐트 감지
│   ├── recipe_agent.py         # 레시피 검색/생성
│   ├── inventory_agent.py      # 냉장고 재고 관리
│   ├── image_agent.py          # 이미지 분석
│   └── quest_agent.py          # 퀘스트 시스템
│
├── core/                       # 핵심 로직
│   ├── graph_builder.py        # LangGraph 워크플로우
│   └── database.py             # SQLite 데이터베이스
│
├── api/                        # FastAPI 서버
│   └── main.py                 # API 엔드포인트
│
├── frontend/                   # Vue.js 프론트엔드
│   ├── src/App.vue
│   ├── public/miri-logo.png
│   └── index.html
│
├── docs/                       # 문서
│   ├── CHANGELOG.md            # 변경 이력
│   ├── FEATURES.md             # 기능 상세 설명
│   ├── SETUP.md                # 설치 가이드
│   └── database_design.md      # DB 설계
│
└── data/                       # 데이터 저장소
    └── nutritionist.db         # SQLite DB
```

---

## 🚀 빠른 시작

### 1. 환경 설정

#### Python 가상환경
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

#### 패키지 설치
```bash
pip install -r requirements.txt
cd frontend && npm install
```

#### 환경변수 설정
`.env` 파일 생성:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 서버 실행

#### 백엔드 (FastAPI)
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### 프론트엔드 (Vue)
```bash
cd frontend
npm run dev
```

### 3. 접속
- **프론트엔드**: http://localhost:5173
- **API 문서**: http://localhost:8000/docs

---

## 📚 문서

자세한 내용은 다음 문서를 참고하세요:

- [설치 가이드](docs/SETUP.md)
- [기능 설명](docs/FEATURES.md)
- [변경 이력](docs/CHANGELOG.md)
- [데이터베이스 설계](docs/database_design.md)

---

## 🏗️ 아키텍처

### 에이전트 워크플로우

```
사용자 입력
    ↓
ChatAgent (인텐트 감지)
    ↓
[분기]
├─ 이미지 업로드 → ImageAgent → InventoryAgent → RecipeAgent
├─ 챗봇 메시지 → ChatAgent → RecipeAgent
└─ 재고 관리 → InventoryAgent
    ↓
DatabaseManager (SQLite)
    ↓
프론트엔드에 결과 반환
```

### 주요 에이전트

#### ChatAgent
- 사용자 메시지에서 인텐트 감지
- `get_recipes`, `manage_inventory`, `general_chat` 분류
- 특정 요리명 및 재료 추출

#### RecipeAgent
- 만개의레시피 API 검색
- LLM 기반 레시피 생성
- 재료 매칭 및 필터링
- 영양 정보 제공

#### InventoryAgent
- 냉장고 재료 관리
- 유통기한 자동 계산
- 적절한 단위 부여

#### ImageAgent
- GPT-4o Vision으로 냉장고 사진 분석
- 재료 및 수량 추출

---

## 🎨 UI/UX 특징

- **다크 모드**: 눈의 피로를 줄이는 어두운 테마
- **그라디언트 디자인**: 모던하고 세련된 인터페이스
- **이모지 아이콘**: 직관적인 사용자 경험
- **반응형**: 모바일/데스크톱 최적화
- **부드러운 애니메이션**: 자연스러운 페이지 전환

---

## 🔐 보안

- `.env` 파일은 Git에서 제외
- API 키는 서버 측에서만 사용
- 사용자 데이터는 로컬에 저장 (localStorage, SQLite)
- CORS 설정으로 안전한 통신

---

## 🧪 테스트

```bash
# 백엔드 테스트
pytest tests/

# API 테스트
# http://localhost:8000/docs 에서 각 엔드포인트 테스트
```

---

## 📦 빌드 및 배포

### 프론트엔드 빌드
```bash
cd frontend
npm run build
# 결과물: frontend/dist/
```

### 백엔드 프로덕션 실행
```bash
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🤝 브랜치 전략

- `main`: 프로덕션 안정 버전
- `dev`: 통합 개발 브랜치
- `feat/*`: 개인 기능 브랜치 → PR → `dev`
- `fix/*`: 버그 수정 브랜치

---

## 📝 라이센스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.

---

## 🙏 기여

프로젝트 개선 아이디어나 버그 리포트는 언제든 환영합니다!

---

**미리 (MIRI)** - 당신의 식탁을 미리 준비합니다 🍳
