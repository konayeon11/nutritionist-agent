# 미리 (MIRI) - 설치 및 실행 가이드

## 📋 시스템 요구사항

### 필수 사항
- **Python**: 3.10 이상
- **Node.js**: 16 이상
- **npm**: 8 이상
- **OpenAI API Key**: GPT-4o 접근 권한

### 권장 사항
- **OS**: macOS, Linux, Windows 10/11
- **RAM**: 4GB 이상
- **저장공간**: 500MB 이상

---

## 🛠️ 설치 방법

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd nutritionist-agent
```

### 2. 백엔드 설정

#### Python 가상환경 생성
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows
```

#### 패키지 설치
```bash
pip install -r requirements.txt
```

#### 환경변수 설정
`.env` 파일을 프로젝트 루트에 생성:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 프론트엔드 설정

#### 프론트엔드 디렉토리로 이동
```bash
cd frontend
```

#### npm 패키지 설치
```bash
npm install
```

---

## 🚀 실행 방법

### 백엔드 서버 실행

프로젝트 루트에서:
```bash
# 가상환경 활성화 (아직 안 했다면)
source .venv/bin/activate

# FastAPI 서버 실행
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**확인**: http://localhost:8000/docs 에서 API 문서 확인

### 프론트엔드 개발 서버 실행

새 터미널에서:
```bash
cd frontend
npm run dev
```

**확인**: http://localhost:5173 에서 앱 실행

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
├── api/                        # FastAPI 서버
│   └── main.py                 # API 엔드포인트
│
├── core/                       # 핵심 로직
│   ├── graph_builder.py        # LangGraph 워크플로우
│   └── database.py             # SQLite 데이터베이스
│
├── data/                       # 데이터 저장소
│   └── nutritionist.db         # SQLite DB (자동 생성)
│
├── docs/                       # 문서
│   ├── CHANGELOG.md            # 변경 이력
│   ├── FEATURES.md             # 기능 설명
│   ├── SETUP.md                # 설치 가이드 (이 파일)
│   ├── SUMMARY.md              # 프로젝트 요약
│   └── database_design.md      # DB 설계
│
├── frontend/                   # Vue.js 프론트엔드
│   ├── src/
│   │   ├── App.vue            # 메인 컴포넌트
│   │   └── main.js            # Vue 진입점
│   ├── public/
│   │   └── miri-logo.png      # MIRI 로고
│   ├── index.html             # HTML 엔트리
│   ├── package.json           # npm 설정
│   └── vite.config.js         # Vite 설정
│
├── tests/                      # 테스트 파일
│
├── .env                        # 환경변수 (생성 필요)
├── .gitignore                  # Git 제외 파일
├── requirements.txt            # Python 패키지 목록
└── README.md                   # 프로젝트 소개
```

---

## 🔧 주요 설정 파일

### requirements.txt (Python 패키지)
```txt
langchain
langgraph
langchain-openai
fastapi
uvicorn
python-dotenv
beautifulsoup4
requests
pydantic
```

### package.json (npm 패키지)
```json
{
  "name": "miri-frontend",
  "version": "1.0.0",
  "dependencies": {
    "vue": "^3.4.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

---

## 🗄️ 데이터베이스 초기화

데이터베이스는 첫 실행 시 자동으로 생성됩니다.

### 수동 초기화 (필요한 경우)
```bash
# Python 인터프리터 실행
python

# 다음 코드 실행
>>> from core.database import DatabaseManager
>>> db = DatabaseManager()
>>> db.close()
>>> exit()
```

### 데이터베이스 리셋
```bash
rm data/nutritionist.db
# 서버 재시작하면 자동으로 새 DB 생성
```

---

## 🧪 테스트

### 백엔드 테스트
```bash
# 프로젝트 루트에서
pytest tests/
```

### API 테스트
브라우저에서 http://localhost:8000/docs 접속 후 각 엔드포인트 테스트

---

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. OpenAI API 키 오류
```
Error: OPENAI_API_KEY not found
```
**해결**: `.env` 파일에 `OPENAI_API_KEY` 설정 확인

#### 2. 포트 이미 사용 중
```
Address already in use: 8000
```
**해결**:
```bash
# 다른 포트로 실행
uvicorn api.main:app --reload --port 8001
```

#### 3. 패키지 설치 오류
```
ERROR: Could not install packages
```
**해결**:
```bash
# pip 업그레이드
pip install --upgrade pip

# 캐시 삭제 후 재설치
pip cache purge
pip install -r requirements.txt
```

#### 4. 프론트엔드 빌드 오류
```
VITE build error
```
**해결**:
```bash
# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install
```

#### 5. CORS 에러
```
Access-Control-Allow-Origin error
```
**해결**: `api/main.py`에서 CORS 설정 확인
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 시에만
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🔐 보안 주의사항

### 개발 환경
- `.env` 파일을 절대 Git에 커밋하지 마세요
- OpenAI API 키는 안전하게 보관하세요
- 개발 시에만 CORS `allow_origins=["*"]` 사용

### 프로덕션 배포
- 환경변수를 서버 환경에서 설정
- CORS 설정을 특정 도메인으로 제한
- HTTPS 사용
- API 키 로테이션 정책 수립

---

## 📦 빌드 및 배포

### 프론트엔드 빌드
```bash
cd frontend
npm run build
```

빌드 결과: `frontend/dist/` 폴더

### 백엔드 배포
```bash
# Gunicorn으로 프로덕션 실행
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📞 지원

문제가 발생하면:
1. 로그 확인 (`터미널 출력`)
2. 이슈 트래커에 버그 리포트
3. 문서 재확인

---

## 📝 라이센스

이 프로젝트는 교육 및 연구 목적으로 제작되었습니다.
