"""
Price Agent - Scrape prices from e-commerce
Responsibility: Find actual prices in Rupiah
"""

from tavily import TavilyClient


class PriceAgent:
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client

    def search_prices(self, product_name: str) -> dict:
        queries = [
            f"{product_name} harga Tokopedia",
            f"{product_name} harga Shopee Indonesia",
            f"{product_name} harga Lazada Indonesia",
            f"{product_name} price list Indonesia Rupiah",
        ]

        prices = []
        for q in queries:
            try:
                result = self.client.search(query=q, max_results=3, search_depth="basic")
                for r in result.get("results", []):
                    content = r.get("content", "")
                    price = self._extract_price(content)
                    if price:
                        prices.append({
                            "source": r.get("title", ""),
                            "url": r.get("url", ""),
                            "price": price,
                            "context": content[:200],
                        })
            except Exception:
                continue

        return {
            "product": product_name,
            "prices": prices[:10],
            "summary": self._summarize_prices(prices),
        }

    def _extract_price(self, text: str) -> str | None:
        import re
        patterns = [
            r"Rp[\s]?[\d.,]+",
            r"IDR[\s]?[\d.,]+",
            r"Rp\s*\d{1,3}(?:\.\d{3})*(?:,\d+)?",
        ]
        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group()
        return None

    def _summarize_prices(self, prices: list[dict]) -> str:
        if not prices:
            return "Harga tidak ditemukan di e-commerce."
        return f"Ditemukan {len(prices)} listing harga dari berbagai sumber."
