FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy the requirements file first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set PYTHONPATH so the components can be imported easily
ENV PYTHONPATH=/app

# Default command if none is provided
# We use entrypoint so arguments can be appended easily (e.g. docker run <image> documents/file.pdf)
ENTRYPOINT ["python", "components/ocr/main.py"]
