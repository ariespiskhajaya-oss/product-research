"""
Competitor Agent - Deep competitor analysis
Responsibility: Find and analyze direct competitors
"""

from tavily import TavilyClient


class CompetitorAgent:
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client

    def analyze_competitors(self, product_name: str) -> dict:
        queries = [
            f"{product_name} competitor comparison",
            f"{product_name} vs alternative printer",
            f"large format printer similar {product_name}",
            f"{product_name} competitor Indonesia market",
        ]

        competitors = []
        seen = set()

        for q in queries:
            try:
                result = self.client.search(query=q, max_results=3, search_depth="advanced")
                for r in result.get("results", []):
                    content = r.get("content", "")
                    brand = self._extract_brand(content, product_name)
                    if brand and brand not in seen:
                        seen.add(brand)
                        competitors.append({
                            "brand": brand,
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": content[:400],
                        })
            except Exception:
                continue

        return {
            "product": product_name,
            "competitors": competitors[:8],
            "market_position": self._assess_position(product_name, competitors),
        }

    def _extract_brand(self, text: str, exclude: str) -> str | None:
        brands = [
            "Roland", "Mimaki", "Mutoh", "Epson", "Canon", "HP",
            "Flora", "Wit-Color", "Hanglory", "Skycolor", "Human",
            "JHF", "DGI", "Dilli", "Xenons", "Seiko", "Durst",
        ]

        text_lower = text.lower()
        for b in brands:
            if b.lower() in text_lower and b.lower() not in exclude.lower():
                return b
        return None

    def _assess_position(self, product_name: str, competitors: list[dict]) -> str:
        if len(competitors) == 0:
            return "Tidak dapat menentukan posisi - kompetitor tidak ditemukan."
        if len(competitors) <= 2:
            return "Market dengan sedikit kompetitor langsung."
        return f"Pasar kompetitif dengan {len(competitors)}+ kompetitor teridentifikasi."
