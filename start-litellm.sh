#!/bin/bash

pip install 'litellm[proxy]'
if curl -sf "$OLLAMA_HOST" > /dev/null; then
    echo 'Ollama: connected'
else
    echo 'Ollama: not reachable — start Ollama on your Mac'
fi

litellm --config litellm-config.yaml --port 4000
