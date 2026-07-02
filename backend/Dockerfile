FROM python:3.12-slim

# tesseract-ocr: the OCR engine app/ocr/service.py shells out to (see
# docs/ARCHITECTURE.md for why Tesseract instead of PaddleOCR)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-hin tesseract-ocr-kan \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# CPU-only torch explicitly - the default index resolves GPU/CUDA wheels
# (nvidia-cuda-*, several GB) even on this CPU-only, GPU-less deployment
# target, which is exactly the "no GPU required" story the rest of this
# stack is built around (see docs/ARCHITECTURE.md).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
