FROM python:3.9-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=api.py
ENV FLASK_RUN_HOST=0.0.0.0
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY . .
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1
CMD ["python3", "api.py"]