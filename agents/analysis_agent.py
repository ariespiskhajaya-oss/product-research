"""
Analysis Agent - Handles AI analysis via OpenAI
Responsibility: Analyze data and generate insights
"""

from openai import OpenAI


class AnalysisAgent:
    def __init__(self, openai_client: OpenAI, system_prompt: str):
        self.client = openai_client
        self.system_prompt = system_prompt
        self.model = "gpt-4o"

    def analyze(self, product_name: str, search_results: list[dict]) -> str:
        web_data = self._format_search_results(search_results)

        user_prompt = f"""Riset produk: {product_name}

=== DATA DARI WEB SEARCH ===
{web_data}

=== INSTRUKSI ===
Analisis data di atas dan hasilkan laporan riset lengkap sesuai format dalam system prompt.
Fokus pada pasar Indonesia. Gunakan data web sebagai dasar analisis.
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=4096,
        )

        return response.choices[0].message.content

    def _format_search_results(self, results: list[dict]) -> str:
        if not results:
            return "Tidak ada data web yang ditemukan."

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(f"[{i}] {r['title']}\n{r['url']}\n{r['content'][:400]}\n")

        return "\n".join(formatted)
