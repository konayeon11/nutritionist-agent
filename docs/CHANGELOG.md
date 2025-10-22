# 변경 이력 (Changelog)

## 2025-10-22 - MIRI 브랜딩 및 UX 대규모 개선

### 🎨 브랜딩
- **서비스명 변경**: "AI 영양사" → "미리 (MIRI)"
  - MIRI = Meal & Intelligence for Real-life Integration
  - 의미: "당신의 식탁을 미리 준비합니다"
- **로고 및 파비콘**: 브랜드 이미지로 교체 (녹색 잎과 주황색 식기 디자인)
- **태그라인**: "당신의 식탁을 미리 준비합니다"

### ✨ 주요 기능 개선

#### 1. 챗봇 레시피 검색 강화
**문제**: "감자전 만들고 싶어"라고 입력해도 관련 없는 레시피 추천
**해결**:
- `ChatAgent`에 `dish_name` 필드 추출 기능 추가
- `RecipeAgent`에서 특정 요리명 우선 검색
- 사용자 프롬프트에서 핵심 키워드 추출 (고기, 닭고기, 돼지고기, 소고기, 생선, 해산물, 채소, 야채)
- LLM 제약조건에 사용자 요청 최우선 반영

**파일**:
- `agents/chat_agent.py`: dish_name 추출 로직
- `agents/recipe_agent.py`: 검색 쿼리 우선순위 및 키워드 추출
- `core/graph_builder.py`: dish_name을 constraints에 전달

#### 2. 네비게이션 개선
**문제**: 챗봇에서 레시피 상세보기 후 돌아가기를 누르면 메인 페이지로 이동
**해결**:
- `previousView` ref 추가하여 레시피 상세보기 이전 페이지 기억
- `closeRecipeDetail()`에서 이전 페이지로 정확히 복귀

**파일**: `frontend/src/App.vue`

#### 3. 챗봇 레시피 목록 영구 표시
**문제**: 챗봇에서 레시피 상세보기 후 돌아오면 추천 레시피 목록이 사라짐
**해결**:
- 채팅 메시지 아래에 `chatLatestRecipes` 기반 레시피 카드 섹션 추가
- 레시피 상세보기 후에도 목록 유지

**파일**: `frontend/src/App.vue`

#### 4. XP 시스템 개선
**문제**: 프로필 저장, 이미지 분석, 레시피 추천 등에서 XP 획득
**해결**:
- 퀘스트 완료 시에만 XP 획득 가능하도록 제한
- `completeQuest()` 외의 모든 `gainXP()` 호출 제거

**파일**: `frontend/src/App.vue`

#### 5. 프로필 폼 UX 개선
**문제**: 입력 필드에 무엇을 입력해야 하는지 불명확
**해결**:
- 이모지 라벨 추가 (🎯 건강 목표, 🍽️ 원하는 식단, 🎂 나이)
- 각 필드 아래 힌트 메시지 추가
- 저장 성공 시 애니메이션 메시지 표시 (alert 제거)
- 입력 필드 스타일링 개선 (focus 상태, 여백, 색상 대비)

**파일**: `frontend/src/App.vue`

#### 6. 냉장고 재료 표시 개선
**추가 기능**:
- 재료별 유통기한 표시 (LLM 기반 자동 계산)
- 적절한 단위 자동 부여 (개, 팩, g, ml, 봉지, 병, 통 등)
- 유통기한 임박 순서로 정렬
- 단위 표시 통일

**파일**: `agents/inventory_agent.py`

#### 7. 퀘스트 시스템 구현
**새로운 기능**:
- 일일/주간 퀘스트 시스템
- 퀘스트 완료 시 XP 획득
- 레벨업 시스템과 연동

**파일**:
- `agents/quest_agent.py` (신규)
- `frontend/src/App.vue`: 퀘스트 UI

### 🛠️ 기술적 개선

#### Git 관리
- `.gitignore` 업데이트:
  - `data/*.db` (개발용 데이터베이스)
  - `frontend/.vite/` (Vite 빌드 캐시)
  - `frontend.backup/` (백업 폴더)
  - `node_modules/`

### 📁 파일 변경 요약

#### 백엔드 (Python)
- `agents/chat_agent.py`: 특정 요리명 추출
- `agents/recipe_agent.py`: 프롬프트 키워드 추출 및 검색 우선순위
- `agents/inventory_agent.py`: 유통기한 및 단위 추가
- `agents/quest_agent.py`: **신규** - 퀘스트 시스템
- `core/graph_builder.py`: dish_name 전달 로직
- `api/main.py`: 엔드포인트 수정

#### 프론트엔드 (Vue.js)
- `frontend/src/App.vue`: 대규모 UI/UX 개선
  - MIRI 브랜딩
  - 네비게이션 개선
  - 프로필 폼 개선
  - 챗봇 레시피 목록
  - XP 시스템 제한
- `frontend/index.html`: 메타 태그 및 파비콘 업데이트
- `frontend/public/miri-logo.png`: **신규** - MIRI 로고

#### 설정 파일
- `.gitignore`: 개발 파일 제외 규칙 추가

### 🐛 버그 수정

1. **챗봇 레시피 검색 오류**: 특정 요리명 무시 → dish_name 추출로 해결
2. **네비게이션 버그**: 잘못된 페이지로 복귀 → previousView 추적으로 해결
3. **레시피 목록 소실**: 상세보기 후 사라짐 → 영구 섹션 추가로 해결
4. **XP 남용**: 모든 행동에서 XP 획득 → 퀘스트 전용으로 제한
5. **프롬프트 무시**: 사용자 요청 미반영 → 키워드 추출 및 LLM 제약조건 추가

---

## 이전 버전

### 2025-10-21 - 프론트엔드 구현 및 채팅 기반 레시피 검색
- Vue.js 프론트엔드 구현
- 채팅 인터페이스 추가
- 이미지 업로드 및 분석 기능
- 레시피 추천 UI

### 2025-10-20 - 메모리 기능 구현
- SQLite 데이터베이스 통합
- 냉장고 인벤토리 관리
- 사용자 프로필 저장

### 2025-10-19 - 초기 설정
- LangGraph 기반 에이전트 구조
- OpenAI GPT-4o 통합
- 만개의레시피 웹 스크래핑
