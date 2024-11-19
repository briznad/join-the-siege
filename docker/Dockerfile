FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install the package in development mode
RUN pip install -e .

# Default command
CMD ["flask", "run", "--host=0.0.0.0"]