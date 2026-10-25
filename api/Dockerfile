FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --system --uid 10001 app
RUN mkdir /data && chown 10001 /data
COPY . .
USER 10001
EXPOSE 8000
CMD ["gunicorn","coach.wsgi:application","--bind","0.0.0.0:8000","--workers","1","--threads","4","--timeout","45","--access-logfile","-"]
