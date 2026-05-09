FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
COPY tests/requirements.txt tests/requirements.txt
RUN pip install --no-cache-dir -r tests/requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV LOG_DIR=/tmp/test-logs

CMD ["python", "-m", "pytest", "-v"]
