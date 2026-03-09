#!/bin/bash

# devcontainer post-create hook
set -e

sudo chown -R vscode:vscode /home/vscode/.aws
# install Claude CLI and AWS CLI (these are not Python-specific)
sudo npm install -g @anthropic-ai/claude-code \
    && curl -fsSL https://claude.ai/install.sh | bash

# create virtual environment and install Python dependencies
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip

# make sure the uv CLI package is installed and synced
pip install uv
uv sync

# pull required models from the host Ollama instance
# echo "Pulling nomic-embed-text..."
# ollama pull nomic-embed-text
# echo "Pulling llama3.2..."
# ollama pull llama3.2

