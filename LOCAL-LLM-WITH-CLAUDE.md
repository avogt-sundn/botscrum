# Using a Local Ollama LLM with Claude Code CLI

Claude Code is hardwired to Anthropic's API, but you can use **LiteLLM** as a proxy that speaks the Anthropic API format while routing to Ollama on the backend.

## Setup

**1. Install LiteLLM**
```bash
pip install 'litellm[proxy]'
```

**2. Start the proxy pointing at your Ollama model**
```bash
# check variable is set
echo $OLLAMA_HOST
# http://host.docker.internal:11434
# start lite llm on devcontainer port 4000
litellm --model ollama/gpt-oss --api_base "$OLLAMA_HOST" --port 4000
# or whatever model you have: ollama/mistral, ollama/qwen2.5, etc.
```

**3. Point Claude Code at the proxy**
```bash
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=fake-key   # required by the CLI, value doesn't matter
```

**4. Launch Claude Code**
```bash
claude
```

## Notes

- The model must be already pulled in Ollama (`ollama pull llama3.2`)
- Tool use / function calling works best with models that support it (e.g. `qwen2.5`, `llama3.1`, `mistral-nemo`)
- Coding-focused models like `qwen2.5-coder` or `deepseek-coder-v2` tend to work better for Claude Code's use case
- Response quality will vary — smaller local models won't match Sonnet's reasoning or tool-use reliability
- If the CLI complains about model names, pass `--model claude-3-5-sonnet-20241022` — LiteLLM will ignore it and use what you configured

## Alternative: lightweight proxies

Some lighter-weight proxy tools exist specifically for this translation if you don't want the full LiteLLM stack. Search for `anthropic ollama proxy` on GitHub for minimal single-file options.
