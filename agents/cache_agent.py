"""
Cache Agent - Store and retrieve research results
Responsibility: Cache research to avoid duplicate work
"""

import json
from pathlib import Path
from datetime import datetime


class CacheAgent:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, product_name: str) -> Path:
        safe_name = product_name.lower().replace(" ", "_").replace("/", "_")
        return self.cache_dir / f"{safe_name}.json"

    def get(self, product_name: str) -> dict | None:
        path = self._get_cache_path(product_name)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cached_at = datetime.fromisoformat(data.get("timestamp", "2000-01-01"))
            age_hours = (datetime.now() - cached_at).total_seconds() / 3600

            if age_hours > 24:
                return None

            return data
        except Exception:
            return None

    def set(self, product_name: str, data: dict):
        path = self._get_cache_path(product_name)
        cache_data = {
            "product": product_name,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
        path.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")

    def clear(self, product_name: str | None = None):
        if product_name:
            path = self._get_cache_path(product_name)
            if path.exists():
                path.unlink()
        else:
            for f in self.cache_dir.glob("*.json"):
                f.unlink()

    def list_cached(self) -> list[str]:
        return [f.stem for f in self.cache_dir.glob("*.json")]
