#!/usr/bin/env python3
"""
LFP Research Agent - Streamlit Web App
User-friendly interface for product research
"""

import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import streamlit as st
from openai import OpenAI
from tavily import TavilyClient

# Load .env for local development
from dotenv import load_dotenv
load_dotenv()

# For Streamlit Cloud: API keys will be set in secrets
# For local: loaded from .env file above

sys.path.insert(0, str(Path(__file__).parent))
from agents.search_agent import SearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.report_agent import ReportAgent
from agents.price_agent import PriceAgent
from agents.distributor_agent import DistributorAgent
from agents.community_agent import CommunityAgent
from agents.competitor_agent import CompetitorAgent
from agents.cache_agent import CacheAgent

SYSTEM_PROMPT_PATH = Path(__file__).parent / "large-format-printer-research-prompt.md"

st.set_page_config(
    page_title="LFP Research Agent",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_secret(key: str) -> str | None:
    """Get secret from Streamlit secrets or environment variable"""
    # Method 1: Streamlit secrets (cloud)
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    # Method 2: Environment variable
    return os.getenv(key)


def init_clients():
    openai_key = get_secret("OPENAI_API_KEY")
    tavily_key = get_secret("TAVILY_API_KEY")

    if not openai_key or not tavily_key:
        st.error("⚠️ API keys belum dikonfigurasi!")
        st.info("Buka **Manage app** → **Secrets** → tambahkan:")
        st.code('''
OPENAI_API_KEY = "sk-xxx"
TAVILY_API_KEY = "tvly-xxx"
        ''')
        st.stop()

    return OpenAI(api_key=openai_key), TavilyClient(api_key=tavily_key)


def load_system_prompt():
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return ""


def run_parallel_search(tavily_client, product_name):
    search_agent = SearchAgent(tavily_client)
    price_agent = PriceAgent(tavily_client)
    distributor_agent = DistributorAgent(tavily_client)
    community_agent = CommunityAgent(tavily_client)
    competitor_agent = CompetitorAgent(tavily_client)

    tasks = {
        "search": lambda: search_agent.search(product_name),
        "price": lambda: price_agent.search_prices(product_name),
        "distributor": lambda: distributor_agent.find_distributors(product_name),
        "community": lambda: community_agent.search_community(product_name),
        "competitor": lambda: competitor_agent.analyze_competitors(product_name),
    }

    results = {}
    progress_bar = st.progress(0, text="Memulai riset...")
    status_text = st.empty()

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_name = {
            executor.submit(func): name for name, func in tasks.items()
        }

        completed = 0
        for future in as_completed(future_to_name):
            name = future_to_name[future]
            try:
                data = future.result()
                results[name] = data
                completed += 1
                progress_bar.progress(
                    completed / len(tasks),
                    text=f"✓ {name.capitalize()} selesai"
                )
            except Exception as e:
                results[name] = {}
                completed += 1
                progress_bar.progress(
                    completed / len(tasks),
                    text=f"⚠ {name.capitalize()} gagal"
                )

    progress_bar.empty()
    status_text.empty()
    return results


def build_analysis_context(all_data):
    context_parts = []

    search_data = all_data.get("search", [])
    if search_data:
        items = [f"[{i+1}] {r.get('title', '')}: {r.get('content', '')[:200]}" for i, r in enumerate(search_data[:8])]
        context_parts.append("=== WEB SEARCH ===\n" + "\n".join(items))

    price_data = all_data.get("price", {})
    if price_data.get("prices"):
        items = [f"- {p.get('price', '')} ({p.get('source', '')[:50]})" for p in price_data["prices"][:5]]
        context_parts.append(f"=== PRICES ===\n{price_data.get('summary', '')}\n" + "\n".join(items))

    distributor_data = all_data.get("distributor", {})
    if distributor_data.get("distributors"):
        items = [f"- {d.get('title', '')[:60]}" for d in distributor_data["distributors"][:5]]
        coverage = distributor_data.get("coverage", {})
        context_parts.append(f"=== DISTRIBUTORS ===\nCoverage: {coverage}\n" + "\n".join(items))

    community_data = all_data.get("community", {})
    if community_data.get("sentiment"):
        context_parts.append(f"=== COMMUNITY SENTIMENT ===\n{community_data.get('sentiment', {})}\nSources: {community_data.get('sources', {})}")

    competitor_data = all_data.get("competitor", {})
    if competitor_data.get("competitors"):
        items = [f"- {c.get('brand', '')}" for c in competitor_data["competitors"][:5]]
        context_parts.append(f"=== COMPETITORS ===\n{competitor_data.get('market_position', 'N/A')}\n" + "\n".join(items))

    return "\n\n".join(context_parts) if context_parts else "Tidak ada data yang tersedia."


def stream_analysis(client, system_prompt, product_name, context):
    user_prompt = f"""Riset produk: {product_name}

{context}

=== INSTRUKSI ===
Analisis data di atas dan hasilkan laporan riset lengkap sesuai format dalam system prompt.
Fokus pada pasar Indonesia. Gunakan data web sebagai dasar analisis.
"""

    stream = client.chat.completions.create(
        model=os.getenv("MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def main():
    st.title("🖨️ LFP Research Agent")
    st.markdown("Multi-Agent AI untuk riset produk Large Format Printer - Pasar Indonesia")

    with st.sidebar:
        st.header("⚙️ Pengaturan")
        st.info("Masukkan nama produk printer untuk memulai riset")

        if st.button("🗑️ Clear Cache"):
            CacheAgent().clear()
            st.success("Cache berhasil dibersihkan!")

        cached = CacheAgent().list_cached()
        if cached:
            st.subheader("📦 Cached Products")
            for c in cached:
                st.text(f"• {c.replace('_', ' ').title()}")

    col1, col2 = st.columns([2, 1])

    with col1:
        product_name = st.text_input(
            "Nama Produk Printer",
            placeholder="Contoh: Epson SC-F9530, Mimaki UJF-7151plus, HITI P322W",
        )

    with col2:
        st.write("")
        st.write("")
        research_btn = st.button("🔍 Mulai Riset", type="primary", use_container_width=True)

    if research_btn and product_name:
        st.divider()

        openai_client, tavily_client = init_clients()
        system_prompt = load_system_prompt()
        cache_agent = CacheAgent()
        report_agent = ReportAgent()

        with st.spinner("📦 Mengecek cache..."):
            cached = cache_agent.get(product_name)

        if cached:
            st.info("📦 Menggunakan data dari cache...")
            all_data = cached.get("data", {})
        else:
            all_data = run_parallel_search(tavily_client, product_name)
            cache_agent.set(product_name, all_data)

        context = build_analysis_context(all_data)

        st.subheader("🤖 AI Analysis")
        analysis_container = st.empty()

        full_response = []
        for chunk in stream_analysis(openai_client, system_prompt, product_name, context):
            full_response.append(chunk)
            analysis_container.markdown("".join(full_response))

        analysis_text = "".join(full_response)

        st.divider()
        st.subheader("📄 Laporan Final")

        filepath = report_agent.format(product_name, analysis_text)

        with open(filepath, "r", encoding="utf-8") as f:
            html_content = f.read()

        st.download_button(
            label="📥 Download HTML Report",
            data=html_content,
            file_name=Path(filepath).name,
            mime="text/html",
            type="primary",
        )

        with st.expander("👁️ Preview Laporan", expanded=True):
            st.components.v1.html(html_content, height=800, scrolling=True)

    elif research_btn:
        st.warning("⚠️ Masukkan nama produk terlebih dahulu!")


if __name__ == "__main__":
    main()
