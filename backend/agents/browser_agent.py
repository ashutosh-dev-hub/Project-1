import webbrowser
import subprocess
import requests
from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from agents.base import BaseAgent
from tools.base import Tool
from memory.db import get_preference

try:
    from ddgs import DDGS
    HAS_DDGS = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DDGS = True
    except ImportError:
        HAS_DDGS = False

class BrowserAgent(BaseAgent):
    def __init__(self):
        super().__init__("BrowserAgent")
        self.register_tool(Tool(
            "search_web", 
            "Search the internet for real-time information, documentation, news, or answers", 
            self.search_web
        ))
        self.register_tool(Tool(
            "open_url", 
            "Open a specific URL in the user's preferred desktop web browser (e.g. Chrome, Brave, Edge)", 
            self.open_url
        ))
        self.register_tool(Tool(
            "extract_page_content", 
            "Fetch and extract readable text content and title from a webpage URL", 
            self.extract_page_content
        ))

    def search_web(self, query: str, max_results: int = 5, **kwargs) -> str:
        """Searches the web via DuckDuckGo and returns title, snippet, and link."""
        if not query:
            raise ValueError("Missing 'query' argument for web search.")

        results = []
        if HAS_DDGS:
            try:
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, max_results=int(max_results)))
                    for r in raw_results:
                        results.append({
                            "title": r.get("title", "No Title"),
                            "snippet": r.get("body", ""),
                            "url": r.get("href", "")
                        })
            except Exception as e:
                # Fallback to direct HTML search if DDGS throws an exception
                results = self._fallback_html_search(query, int(max_results))
        else:
            results = self._fallback_html_search(query, int(max_results))

        if not results:
            return f"No web search results found for query: '{query}'."

        lines = [f"Web Search Results for '{query}':"]
        for i, item in enumerate(results, 1):
            lines.append(f"{i}. {item['title']}\n   URL: {item['url']}\n   Snippet: {item['snippet']}")
        return "\n\n".join(lines)

    def _fallback_html_search(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Fallback search query parser using DuckDuckGo HTML endpoint."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}", headers=headers, timeout=8)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []
            for result in soup.find_all("div", class_="result")[:max_results]:
                title_tag = result.find("a", class_="result__a")
                snippet_tag = result.find("a", class_="result__snippet")
                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                        "url": title_tag.get("href", "")
                    })
            return results
        except Exception:
            return []

    def open_url(self, url: str, browser: Optional[str] = None, **kwargs) -> str:
        """Opens a webpage on the user's desktop in their preferred browser."""
        if not url:
            raise ValueError("Missing 'url' argument.")
            
        # Ensure protocol
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"

        # Detect user's preferred browser from long-term memory
        preferred = browser or get_preference("default_browser", default="").lower()

        # Try PowerShell launch for specific preferred browser
        if preferred in ["brave", "chrome", "msedge", "edge", "firefox"]:
            cmd_browser = "msedge" if preferred == "edge" else preferred
            try:
                proc = subprocess.run(
                    f'powershell -Command "Start-Process \'{cmd_browser}\' \'{url}\'"', 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                if proc.returncode == 0:
                    return f"Successfully opened '{url}' in {preferred.capitalize()} browser."
            except Exception:
                pass

        # Default system fallback
        opened = webbrowser.open(url)
        if opened:
            return f"Successfully opened '{url}' in default system browser."
        return f"Triggered system browser to open '{url}'."

    def extract_page_content(self, url: str, max_chars: int = 3500, **kwargs) -> str:
        """Fetches a webpage, cleans the HTML, and returns the readable text and title."""
        if not url:
            raise ValueError("Missing 'url' argument.")
        if not (url.startswith("http://") or url.startswith("https://")):
            url = f"https://{url}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Remove scripts, styles, forms, and navigation
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"

            # Extract main text
            text_blocks = []
            for p in soup.find_all(["p", "h1", "h2", "h3", "li"]):
                clean_t = p.get_text(separator=" ", strip=True)
                if len(clean_t) > 20:
                    text_blocks.append(clean_t)

            full_text = "\n\n".join(text_blocks)
            if not full_text:
                full_text = soup.get_text(separator=" ", strip=True)

            truncated = full_text[:int(max_chars)]
            suffix = f"\n\n[Content truncated at {max_chars} characters. Total length: {len(full_text)}]" if len(full_text) > int(max_chars) else ""

            return f"Page Title: {title}\nURL: {url}\n\nContent:\n{truncated}{suffix}"
        except Exception as e:
            raise Exception(f"Failed to fetch content from '{url}': {e}")
