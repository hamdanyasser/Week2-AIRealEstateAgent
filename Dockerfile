# ---------- Backend ----------
# Offline build: all wheels are pre-downloaded on the host into ./wheels/.
# pip installs from local files only — zero network needed.

FROM python:3.11-slim

WORKDIR /app

# Copy the lockfile first so dependency installs stay cached
# until requirements change.
COPY requirements.txt .

# Copy pre-downloaded wheels and install offline.
COPY wheels/ /tmp/wheels/
RUN pip install --no-index --find-links=/tmp/wheels/ -r requirements.txt && \
    rm -rf /tmp/wheels/

# Copy application code + trained model artifacts.
COPY app/ app/
COPY models/ models/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
