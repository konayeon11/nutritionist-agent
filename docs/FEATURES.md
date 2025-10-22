# 미리 (MIRI) - 주요 기능

## 📱 개요

**미리 (MIRI)**는 "Meal & Intelligence for Real-life Integration"의 약자로, 사용자의 식탁을 미리 준비하는 AI 영양사 서비스입니다.

**태그라인**: 당신의 식탁을 미리 준비합니다

---

## 🎯 핵심 기능

### 1. 냉장고 스캔 및 재료 분석
- **이미지 분석**: 냉장고 사진을 업로드하면 AI가 재료를 자동 인식
- **재료 관리**: 인식된 재료를 냉장고 인벤토리에 자동 저장
- **유통기한 추적**: 각 재료의 예상 유통기한 자동 계산
- **단위 정규화**: 적절한 단위(개, 팩, g, ml 등) 자동 부여

**기술 스택**:
- OpenAI GPT-4o Vision API
- LangChain 기반 이미지 분석
- SQLite 데이터베이스

### 2. AI 챗봇 레시피 추천
- **자연어 대화**: "감자전 만들고 싶어", "고기 요리 추천해줘" 등 자연스러운 대화
- **특정 요리명 인식**: 특정 요리를 언급하면 해당 요리 우선 검색
- **재료 기반 검색**: 냉장고에 있는 재료를 기반으로 레시피 추천
- **사용자 선호 반영**: "단백질 위주", "20분 내" 등 요구사항 반영

**인텐트 감지**:
- `get_recipes`: 레시피 추천 요청
- `manage_inventory`: 냉장고 재료 관리
- `general_chat`: 일반 대화

### 3. 레시피 검색 및 추천
- **외부 API 연동**: 만개의레시피 웹 스크래핑
- **LLM 기반 생성**: API에 없는 레시피는 GPT-4o가 직접 생성
- **재료 매칭**: 냉장고 재료와 레시피 재료 매칭률 표시
- **영양 정보**: 칼로리, 단백질, 탄수화물, 지방 정보 제공

**검색 우선순위**:
1. 특정 요리명 (dish_name)
2. 사용자 프롬프트 키워드 (고기, 채소 등)
3. 냉장고 상위 재료

### 4. 냉장고 재고 관리
- **실시간 업데이트**: 재료 추가/삭제 즉시 반영
- **유통기한 순 정렬**: 빨리 소비해야 할 재료 우선 표시
- **재고 현황**: 한눈에 보는 냉장고 재료 목록
- **수량 관리**: 재료별 수량 및 단위 표시

### 5. 퀘스트 시스템
- **일일 퀘스트**: 매일 새로운 미션
- **주간 퀘스트**: 장기 목표 달성
- **경험치 시스템**: 퀘스트 완료 시에만 XP 획득
- **레벨 시스템**: XP 누적으로 레벨업

**퀘스트 예시**:
- 첫 냉장고 스캔하기 (+10 XP)
- 레시피 3개 조회하기 (+15 XP)
- 프로필 설정 완료하기 (+20 XP)

### 6. 사용자 프로필
- **건강 목표**: 체중 감량, 근육 증가, 건강 유지 등
- **식단 선호**: 비건, 저탄수화물, 고단백 등
- **개인 정보**: 나이, 성별, 활동량 등
- **로컬 저장**: localStorage 기반 클라이언트 저장

---

## 🏗️ 기술 아키텍처

### 백엔드 (Python)
```
nutritionist-agent/
├── agents/
│   ├── chat_agent.py          # 챗봇 인텐트 감지
│   ├── recipe_agent.py        # 레시피 검색/생성
│   ├── inventory_agent.py     # 재고 관리
│   ├── image_agent.py         # 이미지 분석
│   └── quest_agent.py         # 퀘스트 시스템
├── core/
│   ├── graph_builder.py       # LangGraph 워크플로우
│   └── database.py            # SQLite 관리
└── api/
    └── main.py                # FastAPI 엔드포인트
```

**주요 라이브러리**:
- LangGraph: 에이전트 워크플로우 오케스트레이션
- LangChain: LLM 체이닝 및 프롬프트 관리
- FastAPI: RESTful API 서버
- SQLite: 로컬 데이터베이스
- BeautifulSoup4: 웹 스크래핑
- OpenAI: GPT-4o 모델

### 프론트엔드 (Vue.js)
```
frontend/
├── src/
│   ├── App.vue               # 메인 컴포넌트
│   └── main.js               # Vue 앱 진입점
├── public/
│   └── miri-logo.png         # MIRI 로고
└── index.html                # HTML 엔트리
```

**주요 기술**:
- Vue 3 Composition API
- Vite (빌드 도구)
- Reactive 상태 관리
- localStorage API
- CSS Custom Properties

---

## 🎨 사용자 인터페이스

### 뷰 구조
1. **메인 뷰**: 냉장고 사진 업로드 및 레시피 추천
2. **냉장고 뷰**: 재고 관리 및 유통기한 확인
3. **챗봇 뷰**: AI와 대화하며 레시피 검색
4. **프로필 뷰**: 건강 목표 및 식단 설정
5. **레시피 상세 뷰**: 재료, 조리법, 영양정보

### 디자인 특징
- **다크 모드**: 눈의 피로를 줄이는 어두운 테마
- **그라디언트**: 모던한 그라디언트 디자인
- **이모지**: 직관적인 이모지 아이콘
- **반응형**: 모바일/데스크톱 대응
- **애니메이션**: 부드러운 전환 효과

---

## 🔄 워크플로우

### 이미지 분석 워크플로우
```
사용자 이미지 업로드
    ↓
ImageAgent가 재료 인식 (GPT-4o Vision)
    ↓
InventoryAgent가 유통기한/단위 추가 (GPT-4o)
    ↓
DatabaseManager에 저장 (SQLite)
    ↓
RecipeAgent가 레시피 추천 (만개의레시피 + GPT-4o)
    ↓
사용자에게 결과 표시
```

### 챗봇 워크플로우
```
사용자 메시지 입력
    ↓
ChatAgent가 인텐트 감지 (GPT-4o)
    ↓
[인텐트별 분기]
    ├─ get_recipes → RecipeAgent 호출
    ├─ manage_inventory → InventoryAgent 호출
    └─ general_chat → ChatAgent 응답
    ↓
결과를 챗봇에 표시
```

---

## 📊 데이터 모델

### Inventory (냉장고 재고)
```python
{
    "item_name": str,          # 재료명
    "quantity": str,           # 수량 (단위 포함)
    "added_date": datetime,    # 추가 날짜
    "expiry_date": datetime,   # 유통기한
    "category": str            # 카테고리 (선택)
}
```

### Recipe (레시피)
```python
{
    "title": str,              # 레시피 제목
    "ingredients": list[str],  # 재료 목록
    "instructions": list[str], # 조리 순서
    "cookTime": str,           # 조리 시간
    "servings": str,           # 인분
    "calories": int,           # 칼로리
    "protein": int,            # 단백질 (g)
    "carbs": int,              # 탄수화물 (g)
    "fat": int,                # 지방 (g)
    "image": str,              # 이미지 URL
    "source": str              # 출처 (api/generated)
}
```

### UserProfile (사용자 프로필)
```python
{
    "goal": str,               # 건강 목표
    "diet": str,               # 선호 식단
    "age": int,                # 나이
    "level": int,              # 레벨
    "xp": int,                 # 경험치
    "completedQuests": set     # 완료한 퀘스트 ID
}
```

---

## 🚀 향후 개선 계획

### 단기 목표
- [ ] 레시피 북마크 기능
- [ ] 쇼핑 리스트 자동 생성
- [ ] 주간 식단 계획
- [ ] 알레르기/제한사항 관리

### 중기 목표
- [ ] 음성 인식 레시피 검색
- [ ] 커뮤니티 레시피 공유
- [ ] 영양사 1:1 상담 연결
- [ ] 식단 일기 (푸드 로그)

### 장기 목표
- [ ] 스마트 냉장고 연동
- [ ] AR 기반 조리 가이드
- [ ] 개인 맞춤 영양 분석
- [ ] 건강검진 데이터 연동

---

## 🤝 기여

프로젝트 개선 아이디어나 버그 리포트는 언제든 환영합니다!
