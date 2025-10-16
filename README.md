# ai-nutritionist-agent (skeleton)

협업용 기본 뼈대만 포함합니다. 구현 코드는 각자 feat/* 브랜치에서 진행 후 PR로 dev에 병합합니다.

## 구조
ai-nutritionist-agent/
├─ agents/                # 도메인별 에이전트 (시그니처만)
├─ core/                  # 그래프/메모리/유틸 (시그니처만)
├─ data/                  # 샘플 데이터
├─ api/                   # FastAPI 엔트리포인트 + 스키마 (interface only)
├─ tests/                 # 간단한 테스트 스텁
├─ requirements.txt
└─ .gitignore

## 빠른 실행 (개발용)
pip install -r requirements.txt
uvicorn api.main:app --reload

## 브랜치 전략
- main: 배포/안정
- dev: 통합 개발
- feat/*: 개인 기능 브랜치 → PR → dev
