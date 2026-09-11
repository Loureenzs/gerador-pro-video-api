FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Deno
RUN curl -fsSL https://deno.land/install.sh | sh

ENV PATH="/root/.deno/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .

# Instala dependências da API
RUN pip install --no-cache-dir -r requirements.txt

# Atualiza o yt-dlp para a versão NIGHTLY mais recente
RUN python -m pip install -U --pre "yt-dlp[default]"

COPY . .

# Mostrar versões nos logs durante o build
RUN yt-dlp --version && \
    ffmpeg -version | head -n 1 && \
    deno --version

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
