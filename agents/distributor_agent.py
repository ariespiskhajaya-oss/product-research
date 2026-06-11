"""
Distributor Agent - Find official distributors
Responsibility: Map distributor network per city
"""

from tavily import TavilyClient


class DistributorAgent:
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client

    def find_distributors(self, product_name: str) -> dict:
        brand = product_name.split()[0]

        queries = [
            f"{brand} authorized distributor Indonesia",
            f"{brand} dealer resmi Indonesia",
            f"{brand} distributor Jakarta Surabaya Medan",
            f"{brand} service center Indonesia lokasi",
        ]

        distributors = []
        for q in queries:
            try:
                result = self.client.search(query=q, max_results=3, search_depth="advanced")
                for r in result.get("results", []):
                    distributors.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:300],
                    })
            except Exception:
                continue

        return {
            "product": product_name,
            "brand": brand,
            "distributors": distributors[:15],
            "coverage": self._analyze_coverage(distributors),
        }

    def _analyze_coverage(self, distributors: list[dict]) -> dict:
        cities = ["Jakarta", "Surabaya", "Medan", "Bandung", "Semarang", "Makassar"]
        found = {}

        all_text = " ".join([d.get("content", "") for d in distributors])
        for city in cities:
            found[city] = city.lower() in all_text.lower()

        return {
            "cities_found": [c for c, v in found.items() if v],
            "cities_missing": [c for c, v in found.items() if not v],
        }
