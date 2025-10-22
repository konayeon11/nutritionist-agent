# Docker 배포 가이드

MIRI (미리) 서비스를 Docker로 배포하는 방법입니다.

---

## 📋 사전 요구사항

- **Docker**: 20.10 이상
- **Docker Compose**: 2.0 이상
- **OpenAI API Key**

---

## 🚀 빠른 시작

### 1. 환경변수 설정

프로젝트 루트에 `.env` 파일 생성:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. Docker Compose로 실행

```bash
# 이미지 빌드 및 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 3. 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 4. 중지 및 삭제

```bash
# 컨테이너 중지
docker-compose stop

# 컨테이너 중지 및 삭제
docker-compose down

# 볼륨까지 삭제 (데이터 초기화)
docker-compose down -v
```

---

## 🏗️ 아키텍처

### 서비스 구성

```yaml
services:
  backend:     # FastAPI 백엔드 (포트 8000)
  frontend:    # Vue.js 프론트엔드 (포트 3000)
```

### 데이터 저장

- **SQLite 데이터베이스**: `./data/nutritionist.db` (호스트와 공유)
- **영구 저장**: 호스트의 `data/` 폴더에 마운트

---

## 📁 파일 구조

### Dockerfile (백엔드)

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**특징**:
- Python 3.10 slim 이미지 사용 (경량화)
- requirements.txt 먼저 복사 (캐시 활용)
- FastAPI 서버를 0.0.0.0:8000에서 실행

### frontend/Dockerfile (프론트엔드)

```dockerfile
# 1단계: 빌드
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 2단계: 서빙
FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

**특징**:
- Multi-stage build (빌드 크기 최소화)
- Node 20 alpine 이미지 사용
- `serve`로 정적 파일 서빙

### docker-compose.yml

```yaml
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data  # SQLite DB 영구 저장
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped
```

---

## 🔧 개발 모드

### 코드 변경 실시간 반영

백엔드 개발 시 코드 변경을 실시간 반영하려면:

**docker-compose.override.yml** 생성:

```yaml
services:
  backend:
    volumes:
      - .:/app
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
docker-compose up -d
```

### 프론트엔드 개발 모드

프론트엔드는 Vite 개발 서버를 사용하는 것이 더 빠릅니다:

```bash
# 로컬에서 실행
cd frontend
npm run dev
```

---

## 🛠️ 빌드 최적화

### 이미지 크기 줄이기

#### .dockerignore 활용

```.dockerignore
# Git
.git
.gitignore

# Python 캐시
__pycache__/
.venv/
*.pyc

# 개발 파일
docs/
tests/
frontend.backup/

# 프론트엔드
frontend/node_modules/
frontend/.vite/
```

### 캐시 활용

```bash
# 캐시 없이 새로 빌드
docker-compose build --no-cache

# 특정 서비스만 빌드
docker-compose build backend
```

---

## 🔍 디버깅

### 컨테이너 로그 확인

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend

# 실시간 로그
docker-compose logs -f backend
```

### 컨테이너 내부 접속

```bash
# 백엔드 컨테이너 접속
docker-compose exec backend sh

# 프론트엔드 컨테이너 접속
docker-compose exec frontend sh
```

### 데이터베이스 확인

```bash
# SQLite DB 확인
docker-compose exec backend python -c "
from core.database import DatabaseManager
db = DatabaseManager()
print(db.get_inventory())
db.close()
"
```

---

## 🚢 프로덕션 배포

### 환경변수 설정

프로덕션 환경에서는 `.env` 파일 대신 시스템 환경변수 사용:

```bash
export OPENAI_API_KEY="sk-..."
docker-compose up -d
```

### 리버스 프록시 (Nginx)

**nginx.conf** 예시:

```nginx
server {
    listen 80;
    server_name miri.example.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### HTTPS 설정 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt-get install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d miri.example.com
```

---

## 📊 모니터링

### 리소스 사용량 확인

```bash
# 컨테이너 상태
docker-compose ps

# 리소스 사용량
docker stats

# 특정 컨테이너 리소스
docker stats nutritionist-agent-backend-1
```

### 헬스체크

**docker-compose.yml**에 추가:

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🐛 문제 해결

### 포트 충돌

```bash
# 다른 포트로 실행
docker-compose down
# docker-compose.yml 수정 후
docker-compose up -d
```

### 이미지 빌드 실패

```bash
# 캐시 없이 재빌드
docker-compose build --no-cache

# Docker 시스템 정리
docker system prune -a
```

### 데이터베이스 초기화

```bash
# 데이터 폴더 삭제
rm -rf data/nutritionist.db

# 컨테이너 재시작
docker-compose restart backend
```

---

## 📝 참고사항

- **데이터 백업**: `data/` 폴더를 정기적으로 백업하세요
- **로그 관리**: 로그 로테이션 설정 권장
- **보안**: `.env` 파일을 Git에 커밋하지 마세요
- **성능**: 프로덕션에서는 Gunicorn/Uvicorn workers 조정

---

## 📚 추가 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/docker/)
- [Vue.js 프로덕션 배포](https://vuejs.org/guide/best-practices/production-deployment.html)
