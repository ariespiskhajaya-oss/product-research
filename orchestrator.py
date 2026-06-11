#!/usr/bin/env python3
"""
Multi-Agent Research System for Large Format Printers
Orchestrator: manages agent flow and combines results
Features: Parallel search, Graceful degradation, Retry, Streaming
"""

import os
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from agents.search_agent import SearchAgent
from agents.analysis_agent import AnalysisAgent
from agents.report_agent import ReportAgent
from agents.price_agent import PriceAgent
from agents.distributor_agent import DistributorAgent
from agents.community_agent import CommunityAgent
from agents.competitor_agent import CompetitorAgent
from agents.cache_agent import CacheAgent

load_dotenv()

console = Console()

SYSTEM_PROMPT_PATH = Path(__file__).parent / "large-format-printer-research-prompt.md"

MAX_RETRIES = 3
RETRY_DELAY = 2


def get_clients():
    openai_key = os.getenv("OPENAI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    if not openai_key:
        console.print("[red]OPENAI_API_KEY not set[/red]")
        sys.exit(1)
    if not tavily_key:
        console.print("[red]TAVILY_API_KEY not set[/red]")
        sys.exit(1)

    return OpenAI(api_key=openai_key), TavilyClient(api_key=tavily_key)


def load_system_prompt() -> str:
    if not SYSTEM_PROMPT_PATH.exists():
        console.print(f"[red]System prompt not found: {SYSTEM_PROMPT_PATH}[/red]")
        sys.exit(1)
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def run_with_retry(func, agent_name: str, fallback=None):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func()
        except Exception as e:
            if attempt < MAX_RETRIES:
                console.print(f"[yellow]⚠ {agent_name} attempt {attempt} gagal, retry...[/yellow]")
                time.sleep(RETRY_DELAY * attempt)
            else:
                console.print(f"[red]✗ {agent_name} gagal setelah {MAX_RETRIES} attempts: {e}[/red]")
                return fallback


def run_parallel_search(tavily_client, product_name: str) -> dict:
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
    failed_agents = []

    console.print("\n[cyan]═══ Parallel Data Collection ═══[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Collecting data...", total=len(tasks))

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_name = {
                executor.submit(run_with_retry, func, name, fallback={}): name
                for name, func in tasks.items()
            }

            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    data = future.result()
                    results[name] = data
                    if data:
                        progress.update(task, description=f"[green]✓ {name.capitalize()} done[/green]")
                    else:
                        progress.update(task, description=f"[yellow]⚠ {name.capitalize()} empty[/yellow]")
                        failed_agents.append(name)
                except Exception as e:
                    results[name] = {}
                    failed_agents.append(name)
                    progress.update(task, description=f"[red]✗ {name.capitalize()} failed[/red]")
                progress.advance(task)

    if failed_agents:
        console.print(f"\n[yellow]⚠ Failed agents: {', '.join(failed_agents)}[/yellow]")
        console.print("[yellow]  Continuing with available data...[/yellow]")

    return results


def stream_analysis(client: OpenAI, system_prompt: str, product_name: str, context: str) -> str:
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

    full_response = []
    console.print("\n[cyan]═══ AI Analysis (Streaming) ═══[/cyan]\n")

    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_response.append(content)
            console.print(content, end="")

    console.print("\n")
    return "".join(full_response)


def build_analysis_context(all_data: dict) -> str:
    search_data = all_data.get("search", [])
    price_data = all_data.get("price", {})
    distributor_data = all_data.get("distributor", {})
    community_data = all_data.get("community", {})
    competitor_data = all_data.get("competitor", {})

    context_parts = []

    # Search data
    if search_data:
        search_items = []
        for i, r in enumerate(search_data[:8], 1):
            search_items.append(f"[{i}] {r.get('title', '')}: {r.get('content', '')[:200]}")
        context_parts.append("=== WEB SEARCH ===\n" + "\n".join(search_items))

    # Price data
    if price_data.get("prices"):
        price_items = [f"- {p.get('price', '')} ({p.get('source', '')[:50]})" for p in price_data["prices"][:5]]
        context_parts.append("=== PRICES ===\n" + price_data.get("summary", "") + "\n" + "\n".join(price_items))

    # Distributor data
    if distributor_data.get("distributors"):
        dist_items = [f"- {d.get('title', '')[:60]}" for d in distributor_data["distributors"][:5]]
        coverage = distributor_data.get("coverage", {})
        context_parts.append(f"=== DISTRIBUTORS ===\nCoverage: {coverage}\n" + "\n".join(dist_items))

    # Community data
    if community_data.get("sentiment"):
        sentiment = community_data.get("sentiment", {})
        sources = community_data.get("sources", {})
        context_parts.append(f"=== COMMUNITY SENTIMENT ===\nSentiment: {sentiment}\nSources: {sources}")

    # Competitor data
    if competitor_data.get("competitors"):
        comp_items = [f"- {c.get('brand', '')}" for c in competitor_data["competitors"][:5]]
        position = competitor_data.get("market_position", "N/A")
        context_parts.append(f"=== COMPETITORS ===\n{position}\n" + "\n".join(comp_items))

    return "\n\n".join(context_parts) if context_parts else "Tidak ada data yang tersedia."


def run_pipeline(product_name: str):
    openai_client, tavily_client = get_clients()
    system_prompt = load_system_prompt()

    report_agent = ReportAgent()
    cache_agent = CacheAgent()

    console.print(Panel(f"[bold]{product_name}[/bold]", title="🔍 Target Riset"))

    # Check cache
    cached = cache_agent.get(product_name)
    if cached:
        console.print("[yellow]📦 Menggunakan data dari cache...[/yellow]")
        all_data = cached.get("data", {})
    else:
        all_data = run_parallel_search(tavily_client, product_name)
        cache_agent.set(product_name, all_data)

    # Build context
    context = build_analysis_context(all_data)

    # Stream analysis
    analysis = stream_analysis(openai_client, system_prompt, product_name, context)

    # Format report
    filepath = report_agent.format(product_name, analysis)

    return filepath


def main():
    console.print("[bold cyan]═══ Multi-Agent LFP Research System ═══[/bold cyan]")
    console.print("[dim]7 Agents | Parallel Search | Graceful Degradation | Streaming[/dim]\n")

    if len(sys.argv) > 1:
        product_name = " ".join(sys.argv[1:])
    else:
        product_name = Prompt.ask("[green]Masukkan nama/produk printer[/green]")

    if not product_name.strip():
        console.print("[red]Nama produk tidak boleh kosong[/red]")
        sys.exit(1)

    filepath = run_pipeline(product_name)
    console.print("\n" + "═" * 50 + "\n")
    console.print(f"[bold green]✓ Laporan tersimpan: {filepath}[/bold green]")
    console.print(f"[dim]Buka file di browser untuk melihat laporan[/dim]")


if __name__ == "__main__":
    main()
