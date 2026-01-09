FROM debian:12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python3-pip python3-venv \
         build-essential libpq-dev postgresql-client python3-gdbm \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip
RUN python - <<'PY'
import tomllib
import subprocess

with open('pyproject.toml','rb') as f:
    deps = tomllib.load(f)['project']['dependencies']

subprocess.check_call([
    'pip','install','--no-cache-dir',*deps
])
PY

COPY . /app

RUN chmod +x /app/scripts/wait-for-db.sh

# Create a non-root user and make sure venv and app dir are owned by it.
# Use UID/GID 1000 to match a typical developer user; container services will run as this user.
RUN groupadd -g 1000 app && useradd -m -u 1000 -g app -s /sbin/nologin app \
    && chown -R app:app /app /opt/venv

# Switch to non-root user for runtime
USER app

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
