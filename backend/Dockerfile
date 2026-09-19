FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (detex, pandoc, tectonic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-extra-utils \
    pandoc \
    curl \
    && curl -sSL https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz \
    | tar xz -C /usr/local/bin \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU-only torch: avoids ~4GB of CUDA libraries pulled in by sentence-transformers/gliner
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
