#!/usr/bin/env python3
"""
Coding Bye: token-efficient CLI coding agent client.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_MODEL_BY_PROVIDER = {
    "openai": "gpt-4.1-mini",
    "openrouter": "openai/gpt-4.1-mini",
}

DEFAULT_BASE_URL_BY_PROVIDER = {
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def load_system_prompt(path: Optional[str]) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    default_path = Path(__file__).parent / "system_prompt.txt"
    return default_path.read_text(encoding="utf-8")


def build_headers(provider: str, api_key: str) -> Dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://coding-bye.local"
        headers["X-Title"] = "Coding Bye CLI"
    return headers


def resolve_api_key(args: argparse.Namespace) -> str:
    if args.api_key:
        return args.api_key.strip()
    if args.api_key_env:
        env_value = os.getenv(args.api_key_env, "").strip()
        if env_value:
            return env_value
    return getpass.getpass("Enter API key (hidden): ").strip()


def chat_completion(
    *,
    base_url: str,
    headers: Dict[str, str],
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Dict:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def extract_text(response: Dict) -> str:
    try:
        return response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, AttributeError):
        return json.dumps(response, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="coding-bye",
        description="Token-efficient CLI coding agent for OpenAI-compatible APIs.",
    )
    parser.add_argument("task", nargs="?", help="Task prompt. If omitted, stdin is used.")
    parser.add_argument(
        "--provider",
        default="openrouter",
        help="Provider preset: openrouter | openai | custom",
    )
    parser.add_argument("--base-url", help="Custom OpenAI-compatible base URL.")
    parser.add_argument("--model", help="Model id (provider default if omitted).")
    parser.add_argument(
        "--api-key",
        help="API key string (not recommended in shell history).",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENROUTER_API_KEY",
        help="Environment variable that stores API key (default: OPENROUTER_API_KEY).",
    )
    parser.add_argument("--system-prompt", help="Path to system prompt file.")
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature (default: 0.2).",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1200,
        help="Max completion tokens (default: 1200).",
    )
    parser.add_argument("--json", action="store_true", help="Print raw JSON response.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    provider = args.provider.lower().strip()

    task = args.task or sys.stdin.read().strip()
    if not task:
        print("Error: provide a task argument or pipe text via stdin.", file=sys.stderr)
        return 2

    api_key = resolve_api_key(args)
    if not api_key:
        print("Error: API key is required.", file=sys.stderr)
        return 2

    base_url = args.base_url or DEFAULT_BASE_URL_BY_PROVIDER.get(provider) or "https://api.openai.com/v1"
    model = args.model or DEFAULT_MODEL_BY_PROVIDER.get(provider) or "gpt-4.1-mini"

    system_prompt = load_system_prompt(args.system_prompt)
    headers = build_headers(provider, api_key)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    try:
        response = chat_completion(
            base_url=base_url,
            headers=headers,
            model=model,
            messages=messages,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {error_body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("Request timed out.", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(response, indent=2))
    else:
        print(extract_text(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
