# Coding Bye CLI

Token-efficient CLI coding agent client for OpenAI-compatible APIs (OpenRouter, OpenAI, custom providers).

## What this gives you

- Accepts API key from:
  - `--api-key`
  - env var via `--api-key-env`
  - hidden prompt fallback
- Works with:
  - `--provider openrouter`
  - `--provider openai`
  - `--provider custom --base-url <url>`
- Uses a strong default system prompt in `system_prompt.txt` focused on productivity per token.

## Quick start

```bash
cd coding-bye
python coding_bye.py --help
```

### OpenRouter example

```bash
set OPENROUTER_API_KEY=your_key_here
python coding_bye.py "Build a Python CLI TODO app." --provider openrouter --model openai/gpt-4.1-mini
```

### OpenAI example

```bash
set OPENAI_API_KEY=your_key_here
python coding_bye.py "Refactor this function for clarity." --provider openai --api-key-env OPENAI_API_KEY --model gpt-4.1-mini
```

### Custom OpenAI-compatible provider

```bash
set MY_KEY=your_key_here
python coding_bye.py "Write unit tests for this module." --provider custom --base-url https://your-provider.example/v1 --api-key-env MY_KEY --model your-model-name
```

## Notes

- Keep keys in environment variables where possible.
- You can override the system prompt with `--system-prompt path/to/prompt.txt`.
- Add `--json` to inspect raw API response.
