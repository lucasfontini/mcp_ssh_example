# Usar uma imagem base do Python slim
FROM python:3.11-slim

# Instalar dependências do sistema para paramiko e curl
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Verificar se o uv está instalado (para depuração)
RUN uv --version

# Definir diretório de trabalho
WORKDIR /app

# Copiar o código da aplicação
COPY ssh_server.py .

# Copiar pyproject.toml (se você estiver usando)
COPY pyproject.toml .

# Instalar dependências com uv no ambiente global
RUN uv pip install --system mcp[cli] paramiko

# Expor a porta para SSE
EXPOSE 8000

# Comando para rodar o servidor
CMD ["uv", "run", "ssh_server"]
