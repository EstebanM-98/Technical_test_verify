FROM python:3.10-slim
WORKDIR /app
COPY components/ocr/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["uvicorn", "components.ocr.api:app", "--host", "0.0.0.0", "--port", "8001"]
