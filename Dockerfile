FROM node:22-bookworm-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM python:3.12-slim
COPY api/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY api /app/api
RUN apt-get update && apt-get install -y --no-install-recommends nginx python3 ca-certificates && rm -rf /var/lib/apt/lists/* && useradd --create-home --uid 10001 demo
WORKDIR /app
COPY --from=frontend /src/frontend/dist/studio/browser /app/public
COPY deploy /app/deploy
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python3", "/app/deploy/start.py"]
