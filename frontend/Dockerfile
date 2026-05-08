FROM python:3.10-slim
WORKDIR /app
# Need to install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y libmupdf-dev && rm -rf /var/lib/apt/lists/*
COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
