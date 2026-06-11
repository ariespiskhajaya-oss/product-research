"""
Community Agent - Find reviews and sentiment
Responsibility: Gather community feedback from YouTube, forums, groups
"""

from tavily import TavilyClient


class CommunityAgent:
    def __init__(self, tavily_client: TavilyClient):
        self.client = tavily_client

    def search_community(self, product_name: str) -> dict:
        queries = [
            f"{product_name} review YouTube Indonesia",
            f"{product_name} pengalaman user Indonesia",
            f"{product_name} komunitas print Indonesia",
            f"{product_name} forum review feedback",
        ]

        reviews = []
        for q in queries:
            try:
                result = self.client.search(query=q, max_results=3, search_depth="advanced")
                for r in result.get("results", []):
                    reviews.append({
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "content": r.get("content", "")[:400],
                        "source_type": self._detect_source(r.get("url", "")),
                    })
            except Exception:
                continue

        return {
            "product": product_name,
            "reviews": reviews[:12],
            "sentiment": self._analyze_sentiment(reviews),
            "sources": self._categorize_sources(reviews),
        }

    def _detect_source(self, url: str) -> str:
        url_lower = url.lower()
        if "youtube" in url_lower:
            return "YouTube"
        elif "forum" in url_lower or "kaskus" in url_lower:
            return "Forum"
        elif "review" in url_lower:
            return "Review Site"
        elif "blog" in url_lower:
            return "Blog"
        return "Other"

    def _analyze_sentiment(self, reviews: list[dict]) -> dict:
        positive = ["bagus", "puas", "recommended", "worth", "mantap", "ok", "good", "great"]
        negative = ["jelek", "rusak", "masalah", "error", "buruk", "bad", "problem"]

        all_text = " ".join([r.get("content", "").lower() for r in reviews])
        pos_count = sum(1 for w in positive if w in all_text)
        neg_count = sum(1 for w in negative if w in all_text)

        if pos_count > neg_count:
            return {"status": "positive", "confidence": min(pos_count / 10, 1.0)}
        elif neg_count > pos_count:
            return {"status": "negative", "confidence": min(neg_count / 10, 1.0)}
        return {"status": "neutral", "confidence": 0.5}

    def _categorize_sources(self, reviews: list[dict]) -> dict:
        categories = {}
        for r in reviews:
            t = r.get("source_type", "Other")
            categories[t] = categories.get(t, 0) + 1
        return categories
