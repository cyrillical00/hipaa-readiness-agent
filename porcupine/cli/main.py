"""
Porcupine CLI — prediction market signal engine.

Commands:
  porcupine fetch                  Pull top N active Polymarket markets
  porcupine signal <market_id>     Run LLM ensemble on a single market
  porcupine compare [--top N]      Run ensemble across top N markets by volume
  porcupine auth login             Supabase magic link login
  porcupine auth status            Show current login status
  porcupine auth logout            Clear stored session
"""

from __future__ import annotations

import sys
import os

# Allow running from project root: python -m cli.main or python cli/main.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich import box
from rich.text import Text

from ingestion.polymarket import fetch_markets, fetch_market, Market
from signals.engine import run_ensemble, EnsembleResult, ModelSignal
from db import supabase_client as db
from auth import session as auth_session

app = typer.Typer(
    name="porcupine",
    help="Private prediction market signal engine.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
auth_app = typer.Typer(help="Authentication commands.", no_args_is_help=True)
app.add_typer(auth_app, name="auth")

console = Console()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _format_prob(p: Optional[float], as_pct: bool = True) -> str:
    if p is None:
        return "[dim]N/A[/dim]"
    if as_pct:
        return f"{p * 100:.1f}%"
    return f"{p:.3f}"


def _delta_text(delta: Optional[float]) -> Text:
    """Color-code the signal delta: green = model > market, red = model < market."""
    if delta is None:
        return Text("N/A", style="dim")
    pct = delta * 100
    sign = "+" if pct >= 0 else ""
    style = "bold green" if pct > 1 else ("bold red" if pct < -1 else "dim")
    return Text(f"{sign}{pct:.1f}%", style=style)


def _confidence_text(conf: Optional[str]) -> Text:
    styles = {"high": "bold cyan", "medium": "yellow", "low": "dim red"}
    if not conf:
        return Text("N/A", style="dim")
    return Text(conf.upper(), style=styles.get(conf.lower(), "dim"))


def _truncate(s: str, n: int = 60) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


# ---------------------------------------------------------------------------
# fetch command
# ---------------------------------------------------------------------------

@app.command()
def fetch(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of markets to fetch."),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip Supabase upsert."),
):
    """Pull top N active Polymarket markets sorted by volume."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Fetching Polymarket markets…", total=None)
        try:
            markets = fetch_markets(limit=limit)
        except RuntimeError as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            raise typer.Exit(1)

    if not markets:
        console.print("[yellow]No active markets returned.[/yellow]")
        raise typer.Exit(0)

    # Cache in Supabase (best-effort — don't fail the command if creds missing)
    if not no_cache:
        try:
            rows = [
                {
                    "id": m.condition_id,
                    "question": m.question,
                    "implied_prob": m.implied_prob,
                    "volume": m.volume,
                    "end_date": m.end_date,
                }
                for m in markets
            ]
            db.upsert_markets(rows)
        except Exception:
            pass  # silently skip cache write if Supabase not configured

    table = Table(
        title=f"Polymarket Markets (top {len(markets)} by volume)",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Market ID", style="dim", no_wrap=True, max_width=20)
    table.add_column("Question", max_width=55)
    table.add_column("Implied Prob", justify="right")
    table.add_column("Volume (USDC)", justify="right")
    table.add_column("Ends", max_width=12)

    for m in markets:
        vol_str = f"${m.volume:,.0f}" if m.volume else "—"
        end_str = (m.end_date or "—")[:10]
        table.add_row(
            m.condition_id[:18] + "…" if len(m.condition_id) > 18 else m.condition_id,
            _truncate(m.question, 55),
            _format_prob(m.implied_prob),
            vol_str,
            end_str,
        )

    console.print(table)
    console.print(f"\n[dim]Use [bold]porcupine signal <market_id>[/bold] to run the LLM ensemble on any market.[/dim]")


# ---------------------------------------------------------------------------
# signal command
# ---------------------------------------------------------------------------

@app.command()
def signal(
    market_id: str = typer.Argument(..., help="Polymarket condition_id."),
    no_store: bool = typer.Option(False, "--no-store", help="Skip Supabase write."),
):
    """Run the LLM ensemble on a single market and display the signal."""
    # Fetch market data
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Fetching market {market_id[:12]}…", total=None)
        try:
            market = fetch_market(market_id)
        except (ValueError, RuntimeError) as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            raise typer.Exit(1)

    console.rule(f"[bold cyan]Signal: {_truncate(market.question, 70)}")
    console.print(
        f"  [dim]Market ID:[/dim] {market.condition_id}\n"
        f"  [dim]Market price (implied prob):[/dim] [bold]{_format_prob(market.implied_prob)}[/bold]\n"
        f"  [dim]Ends:[/dim] {(market.end_date or 'N/A')[:10]}\n"
    )

    # Run ensemble with progress spinner per model
    result = EnsembleResult(market_id=market.condition_id)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        from signals.engine import MODELS, _query_model
        for model_cfg in MODELS:
            task = progress.add_task(f"Querying {model_cfg['label']}…", total=None)
            sig = _query_model(model_cfg, market)
            result.signals.append(sig)
            progress.remove_task(task)

    # Display results table
    table = Table(
        title="LLM Signal Ensemble",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Model", style="bold", min_width=24)
    table.add_column("Estimate", justify="right")
    table.add_column("vs Market", justify="right")
    table.add_column("Confidence")
    table.add_column("Latency")
    table.add_column("Rationale", max_width=45)

    for sig in result.signals:
        if sig.ok:
            delta = market.delta(sig.estimate)
            table.add_row(
                sig.model_label,
                _format_prob(sig.estimate),
                _delta_text(delta),
                _confidence_text(sig.confidence),
                f"{sig.latency_ms}ms",
                _truncate(sig.rationale or "", 45),
            )
        else:
            table.add_row(
                sig.model_label,
                "[dim]—[/dim]",
                "[dim]—[/dim]",
                "[dim]—[/dim]",
                f"{sig.latency_ms}ms",
                f"[red]{_truncate(sig.error or 'Error', 45)}[/red]",
            )

    console.print(table)

    mean = result.mean_estimate
    if mean is not None:
        mean_delta = market.delta(mean)
        console.print(
            f"\n  [bold]Ensemble mean:[/bold] {_format_prob(mean)}  "
            f"delta: {_delta_text(mean_delta)}\n"
        )

    # Store in Supabase if authenticated
    if not no_store:
        try:
            sess = auth_session.load_session()
            if sess:
                run_id = db.insert_signal_run(
                    market_id=market.condition_id,
                    results=result.to_json_list(),
                    access_token=sess["access_token"],
                    user_id=sess["user_id"],
                )
                console.print(f"[dim]Stored run → {run_id}[/dim]")
        except Exception as exc:
            console.print(f"[dim yellow]Warning: could not store run — {exc}[/dim yellow]")


# ---------------------------------------------------------------------------
# compare command
# ---------------------------------------------------------------------------

@app.command()
def compare(
    top: int = typer.Option(10, "--top", "-n", help="Number of markets to compare."),
    no_store: bool = typer.Option(False, "--no-store", help="Skip Supabase writes."),
):
    """
    Run the LLM ensemble across the top N markets by volume.
    Output is ranked by abs(ensemble_mean - implied_prob) descending.
    """
    console.print(f"[bold cyan]Fetching top {top} markets by volume…[/bold cyan]")

    try:
        markets = fetch_markets(limit=top)
    except RuntimeError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(1)

    if not markets:
        console.print("[yellow]No markets returned.[/yellow]")
        raise typer.Exit(0)

    # Cache markets (best-effort)
    try:
        rows = [
            {"id": m.condition_id, "question": m.question,
             "implied_prob": m.implied_prob, "volume": m.volume, "end_date": m.end_date}
            for m in markets
        ]
        db.upsert_markets(rows)
    except Exception:
        pass

    results: list[tuple[Market, EnsembleResult]] = []

    for i, market in enumerate(markets, 1):
        console.print(
            f"\n[{i}/{len(markets)}] [bold]{_truncate(market.question, 55)}[/bold]  "
            f"[dim]{_format_prob(market.implied_prob)}[/dim]"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            from signals.engine import MODELS, _query_model
            result = EnsembleResult(market_id=market.condition_id)
            for model_cfg in MODELS:
                progress.add_task(f"  {model_cfg['label']}…", total=None)
                sig = _query_model(model_cfg, market)
                result.signals.append(sig)

        results.append((market, result))

        if not no_store:
            try:
                sess = auth_session.load_session()
                if sess:
                    db.insert_signal_run(
                        market_id=market.condition_id,
                        results=result.to_json_list(),
                        access_token=sess["access_token"],
                        user_id=sess["user_id"],
                    )
            except Exception:
                pass

    # Sort by absolute delta descending
    def sort_key(pair: tuple[Market, EnsembleResult]) -> float:
        m, r = pair
        mean = r.mean_estimate
        if mean is None or m.implied_prob is None:
            return 0.0
        return abs(mean - m.implied_prob)

    results.sort(key=sort_key, reverse=True)

    # Summary table
    console.print()
    console.rule("[bold cyan]Compare Results — Ranked by Signal Strength")

    table = Table(box=box.ROUNDED, show_lines=False)
    table.add_column("#", justify="right", style="dim", width=3)
    table.add_column("Question", max_width=50)
    table.add_column("Market", justify="right")
    table.add_column("Ensemble", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("OK / Total")
    table.add_column("Volume", justify="right")

    for rank, (market, result) in enumerate(results, 1):
        mean = result.mean_estimate
        ok_count = sum(1 for s in result.signals if s.ok)
        total = len(result.signals)
        delta = market.delta(mean) if mean is not None else None
        vol_str = f"${market.volume:,.0f}" if market.volume else "—"

        table.add_row(
            str(rank),
            _truncate(market.question, 50),
            _format_prob(market.implied_prob),
            _format_prob(mean),
            _delta_text(delta),
            f"{ok_count}/{total}",
            vol_str,
        )

    console.print(table)


# ---------------------------------------------------------------------------
# auth commands
# ---------------------------------------------------------------------------

@auth_app.command("login")
def auth_login(
    email: str = typer.Option(..., "--email", "-e", prompt="Email address", help="Your invited email."),
):
    """Send a magic link and log in via browser callback."""
    console.print(f"[cyan]Sending magic link to {email}…[/cyan]")
    try:
        sess = auth_session.login(email)
    except RuntimeError as exc:
        console.print(f"[bold red]Login failed:[/bold red] {exc}")
        raise typer.Exit(1)

    console.print(
        f"[bold green]Logged in as {sess['email']}[/bold green]  "
        f"[dim](user_id: {sess['user_id'][:8]}…)[/dim]"
    )


@auth_app.command("status")
def auth_status():
    """Show current login status."""
    sess = auth_session.load_session()
    if sess:
        console.print(
            f"[bold green]Logged in:[/bold green] {sess['email']}  "
            f"[dim](user_id: {sess['user_id'][:8]}…)[/dim]"
        )
    else:
        console.print("[yellow]Not logged in.[/yellow]  Run: [bold]porcupine auth login[/bold]")


@auth_app.command("logout")
def auth_logout():
    """Clear the stored session from keychain."""
    auth_session.clear_session()
    console.print("[green]Logged out.[/green]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
