FROM python:3.11-slim

WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
COPY main.py .

# 기본 포트 환경변수 설정 (Google Cloud Run 호환)
ENV PORT=8080
EXPOSE 8080

# uvicorn 실행 (환경변수 PORT 지원)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
