FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 app
COPY . .
USER 10001
RUN python worker.py download-files
CMD ["python","worker.py","start"]
