FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    curl \
    && npm install -g configurable-http-proxy \
    && apt-get purge -y --auto-remove \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    jupyterhub \
    jupyterlab \
    notebook

RUN useradd -m -s /bin/bash admin

RUN mkdir -p /srv/jupyterhub
WORKDIR /srv/jupyterhub

EXPOSE 8000

CMD ["jupyterhub", "-f", "/srv/jupyterhub/jupyterhub_config.py"]
