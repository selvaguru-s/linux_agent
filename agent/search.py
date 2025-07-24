import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# Trusted domains for Linux/DevOps tasks
TRUSTED_SITES = [
    "askubuntu.com", "unix.stackexchange.com", "serverfault.com",
    "stackoverflow.com", "ubuntu.com", "man7.org", "tldp.org",
    "linuxize.com", "phoenixnap.com", "digitalocean.com", "redhat.com", "archlinux.org"
]

# Trust scores for domain prioritization
DOMAIN_TRUST_SCORE = {
    "ubuntu.com": 10,
    "redhat.com": 10,
    "man7.org": 9,
    "askubuntu.com": 9,
    "unix.stackexchange.com": 9,
    "serverfault.com": 8,
    "digitalocean.com": 8,
    "phoenixnap.com": 8,
    "linuxize.com": 7,
    "tldp.org": 6,
    "archlinux.org": 6,
    "stackoverflow.com": 5
}


def build_trusted_query(task: str, context: dict) -> str:
    """
    Constructs a search query string limited to trusted domains and specific to system context.
    """
    os_part = f" on {context.get('os', '')} {context.get('os_version', '')}".strip()
    domain_filter = " OR ".join([f"site:{site}" for site in TRUSTED_SITES])
    return f"bash command to {task}{os_part} {domain_filter}"



def extract_domain(url: str) -> str:
    """
    Extracts domain from a URL, removing 'www.'
    """
    return urlparse(url).netloc.replace("www.", "")


def search_web(task: str, context: dict, max_results: int = 6) -> list[str]:
    """
    Performs a DuckDuckGo search using system context, and returns ranked and filtered snippets.
    """
    query = build_trusted_query(task, context)
    url = f"https://html.duckduckgo.com/html/?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"⚠️ DuckDuckGo request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    raw_results = []

    for result in soup.select("a.result__a"):
        href = result.get("href")
        if not href:
            continue
        domain = extract_domain(href)
        score = DOMAIN_TRUST_SCORE.get(domain, 0)
        snippet_tag = result.find_parent("div", class_="result").select_one(".result__snippet")
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        if snippet and len(snippet.split()) > 5:
            raw_results.append((score, snippet))

    sorted_results = sorted(raw_results, key=lambda x: x[0], reverse=True)
    return [snippet for _, snippet in sorted_results[:max_results]]
