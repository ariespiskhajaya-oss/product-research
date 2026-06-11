"""
Search Agent - Handles web search via Tavily
Responsibility: Find product data from the web
"""

from tavily import TavilyClient


class SearchAgent:
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client

    def search(self, product_name: str) -> list[dict]:
        queries = [
            f"{product_name} large format printer Indonesia harga distributor",
            f"{product_name} specifications review spesifikasi",
            f"{product_name} vs competitor Indonesia market comparison",
            f"{product_name} spare part service after sales Indonesia",
        ]

        all_results = []
        seen_urls = set()

        for q in queries:
            try:
                result = self.client.search(query=q, max_results=3, search_depth="advanced")
                for r in result.get("results", []):
                    url = r.get("url", "")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            "title": r.get("title", ""),
                            "url": url,
                            "content": r.get("content", ""),
                        })
            except Exception:
                continue

        return all_results
