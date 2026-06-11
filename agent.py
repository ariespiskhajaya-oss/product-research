#!/usr/bin/env python3
"""
Large Format Printer Research Agent
Input: Product name
Output: Comprehensive market research report
Tools: Tavily (web search) + OpenAI (analysis)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

load_dotenv()

console = Console()

SYSTEM_PROMPT_PATH = Path(__file__).parent / "large-format-printer-research-prompt.md"


def load_system_prompt() -> str:
    if not SYSTEM_PROMPT_PATH.exists():
        console.print(f"[red]System prompt not found: {SYSTEM_PROMPT_PATH}[/red]")
        sys.exit(1)
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console.print("[red]OPENAI_API_KEY not set in .env or environment[/red]")
        sys.exit(1)
    return OpenAI(api_key=api_key)


def get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        console.print("[red]TAVILY_API_KEY not set in .env or environment[/red]")
        sys.exit(1)
    return TavilyClient(api_key=api_key)


def search_product_info(tavily: TavilyClient, product_name: str) -> str:
    queries = [
        f"{product_name} large format printer Indonesia harga distributor",
        f"{product_name} specifications review",
        f"{product_name} vs competitor Indonesia market",
        f"large format printer {product_name} spare part service Indonesia",
    ]

    all_results = []
    for q in queries:
        try:
            result = tavily.search(query=q, max_results=3, search_depth="advanced")
            for r in result.get("results", []):
                all_results.append(f"**{r['title']}**\n{r['content'][:500]}")
        except Exception as e:
            console.print(f"[yellow]Search warning: {e}[/yellow]")

    return "\n\n---\n\n".join(all_results) if all_results else "No web results found."


def research_product(client: OpenAI, tavily: TavilyClient, system_prompt: str, product_name: str) -> str:
    console.print("[cyan]🔍 Mencari data produk dari web...[/cyan]")
    web_data = search_product_info(tavily, product_name)

    user_prompt = f"""Riset produk: {product_name}

=== DATA DARI WEB SEARCH ===
{web_data}

=== INSTRUKSI ===
Gunakan data web search di atas sebagai dasar analisis. Jika data tidak cukup, gunakan pengetahuan umum Anda tentang industri LFP.
"""

    console.print("[cyan]🤖 AI sedang menganalisis...[/cyan]")
    response = client.chat.completions.create(
        model=os.getenv("MODEL", "gpt-4o"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content


def main():
    console.print("[bold cyan]Large Format Printer Research Agent[/bold cyan]")
    console.print("[dim]Tools: Tavily (web search) + ChatGPT (analysis)[/dim]\n")

    system_prompt = load_system_prompt()
    client = get_client()
    tavily = get_tavily_client()

    if len(sys.argv) > 1:
        product_name = " ".join(sys.argv[1:])
    else:
        product_name = Prompt.ask("[green]Masukkan nama/produk printer[/green]")

    if not product_name.strip():
        console.print("[red]Nama produk tidak boleh kosong[/red]")
        sys.exit(1)

    console.print(f"\n[yellow]Meriset: {product_name}...[/yellow]\n")

    with console.status("[bold green]Proses riset berjalan..."):
        result = research_product(client, tavily, system_prompt, product_name)

    console.print(Markdown(result))


if __name__ == "__main__":
    main()
