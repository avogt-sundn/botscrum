#!/bin/bash

export ANTHROPIC_BASE_URL=http://host.docker.internal:1234
export ANTHROPIC_AUTH_TOKEN=lmstudio
claude --model openai/gpt-oss-20b
