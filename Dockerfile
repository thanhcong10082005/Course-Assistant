# Course Assistant - Trợ lý hỗ trợ học tập môn NLP (CO3085)
#
# Hệ thống chạy hoàn toàn bằng thư viện chuẩn của Python: image không cần
# bất kỳ gói NLP nào (không NLTK, không spaCy, không Transformers).

FROM python:3.11-slim

WORKDIR /app

# The runtime needs no third party package.  The base image is enough.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application.  The output/ directory is *not* copied: it is
# generated when the container starts, so an empty output/ can never break
# the build.
COPY src/ ./src/
COPY data/ ./data/
COPY models/ ./models/
COPY input/ ./input/
COPY scripts/ ./scripts/

# The official test set lives in tests/data/.  Both src/evaluation.py and
# scripts/baseline.py read it, so the evaluation report inside the container
# would silently drop the 34 official cases if this directory were missing.
COPY tests/data/ ./tests/data/

RUN mkdir -p output

ENV PYTHONPATH=/app
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1

# Generate the nine artefacts of output/ and then verify the installation.
CMD ["python", "-m", "src.main", "--mode", "generate"]
