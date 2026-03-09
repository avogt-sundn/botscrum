#!/bin/bash

# devcontainer post-start hook

sudo chown -R vscode:vscode /home/vscode/.aws

if curl -sf "$OLLAMA_HOST" > /dev/null; then
    echo 'Ollama: connected'
else
    echo 'Ollama: not reachable — start Ollama on your Mac'
fi

litellm --model ollama/gpt-oss --api_base "$OLLAMA_HOST" --port 4000 &
