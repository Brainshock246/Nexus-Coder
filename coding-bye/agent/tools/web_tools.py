from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from typing import Any, Dict

from agent.tools.base import Tool


def _fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CodingByeAgent/2.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def build_web_tools() -> list[Tool]:
    def web_search(payload: Dict[str, Any]) -> Dict[str, Any]:
        query = str(payload["query"])
        url = "https://duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        body = _fetch(url)
        links = re.findall(r'<a rel="nofollow" class="result__a" href="(.*?)">(.*?)</a>', body)
        parsed = [
            {"url": html.unescape(link), "title": re.sub("<.*?>", "", html.unescape(title))}
            for link, title in links[:5]
        ]
        return {"query": query, "results": parsed}

    def web_scraper(payload: Dict[str, Any]) -> Dict[str, Any]:
        url = str(payload["url"])
        body = _fetch(url)
        text = re.sub("<script.*?</script>", "", body, flags=re.S)
        text = re.sub("<style.*?</style>", "", text, flags=re.S)
        text = re.sub("<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return {"url": url, "content": text[:6000]}

    return [
        Tool(
            name="web_search",
            description="Search the web and return top results",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            run=web_search,
        ),
        Tool(
            name="web_scraper",
            description="Fetch and extract text from a webpage URL",
            input_schema={"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
            run=web_scraper,
        ),
    ]

