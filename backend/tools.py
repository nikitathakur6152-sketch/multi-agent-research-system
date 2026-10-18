"""Search the web with Tavily and scrape a page from the terminal or an agent."""

import argparse
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
from rich import print
from tavily import TavilyClient


# Load the project's .env even when this file is launched from another directory.
load_dotenv(Path(__file__).resolve().with_name(".env"))


def _get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is missing. Add it to the project's .env file."
        )
    return TavilyClient(api_key=api_key)


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic."""
    results = _get_tavily_client().search(query=query, max_results=5)
    entries = []
    for result in results["results"]:
        entries.append(
            f"Title: {result['title']}\n"
            f"URL: {result['url']}\n"
            f"Snippet: {result['content'][:300]}"
        )
    return "\n\n------\n\n".join(entries)


@tool
def scrape_url(url: str) -> str:
    """Scrape and return a clean version of a URL's text."""
    response = requests.get(
        url, timeout=10, headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)[:3000]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search the web with Tavily. A query is optional."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="what is the latest news on AI technology?",
        help="search query (defaults to a recent AI news search)",
    )
    args = parser.parse_args()

    try:
        print(web_search.invoke(args.query))
    except Exception as error:
        print(f"[red]Search failed:[/red] {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
