# ---------- Base Image ----------
FROM python:3.12-slim

# ---------- Working Directory ----------
WORKDIR /app

# ---------- Install system dependencies ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ---------- Copy dependency list ----------
COPY requirements.txt .

# ---------- Install Python dependencies ----------
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Copy project files ----------
COPY . .

# ---------- Expose port ----------
EXPOSE 8000

# ---------- Default command ----------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
