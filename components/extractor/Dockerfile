# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Copy requirements
COPY components/extractor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest
COPY . /app

# Run main.py when the container launches
CMD ["uvicorn", "components.extractor.api:app", "--host", "0.0.0.0", "--port", "8002"]
