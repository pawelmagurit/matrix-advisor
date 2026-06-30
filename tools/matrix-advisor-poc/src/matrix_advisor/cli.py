import json
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from matrix_advisor.config import EXTRAL_JSON, SAMPLE_DIR, ensure_data_dirs
from matrix_advisor.db import init_db
from matrix_advisor.embeddings.encoder import embedding_backend_name
from matrix_advisor.index.builder import (
    build_embedding_index,
    build_geometric_index,
    get_index_stats,
    query_similar,
)
from matrix_advisor.ingestion.import_csv import ingest_matrices, ingest_profiles
from matrix_advisor.ingestion.import_extral_json import ingest_extral_json
from matrix_advisor.ingestion.sample_data import generate_sample_data
from matrix_advisor.models import QueryResponse, SimilarityMethod
from matrix_advisor.dxf.pipeline import import_dxf_directory, process_dxf_file
from matrix_advisor.normalization.pipeline import normalize_all

app = typer.Typer(
    name="matrix-advisor",
    help="PoC: profile pictogram similarity for extrusion die advisory",
)
console = Console()


class MethodChoice(str, Enum):
    geometric = "geometric"
    embedding = "embedding"
    all = "all"


@app.command("init-db")
def cmd_init_db() -> None:
    """Initialize SQLite database and data directories."""
    path = init_db()
    ensure_data_dirs()
    console.print(f"[green]Database ready:[/green] {path}")


@app.command("sample-data")
def cmd_sample_data(
    count: int = typer.Option(24, help="Number of synthetic profiles"),
) -> None:
    """Generate synthetic pictograms and CSV manifests under data/sample/."""
    out = generate_sample_data(count=count)
    console.print(f"[green]Sample data written to[/green] {out}")


@app.command("ingest")
def cmd_ingest(
    manifest: Path = typer.Option(..., exists=True, help="profiles.csv path"),
    pictograms_dir: Path = typer.Option(..., exists=True, help="Directory with pictogram files"),
    matrices: Path | None = typer.Option(None, exists=True, help="Optional matrices.csv"),
) -> None:
    """Import profiles and optional matrix history from CSV exports."""
    init_db()
    pstats = ingest_profiles(manifest, pictograms_dir)
    console.print(f"Profiles: {pstats}")
    if matrices:
        mstats = ingest_matrices(matrices)
        console.print(f"Matrices: {mstats}")


@app.command("normalize")
def cmd_normalize() -> None:
    """Normalize all ingested pictograms to canonical masks."""
    stats = normalize_all()
    console.print(f"[green]Normalization:[/green] {stats}")


@app.command("build-index")
def cmd_build_index(
    method: MethodChoice = typer.Option(MethodChoice.all, "--method", "-m"),
) -> None:
    """Build similarity index(es)."""
    if method in (MethodChoice.geometric, MethodChoice.all):
        path = build_geometric_index()
        console.print(f"[green]Geometric index:[/green] {path}")
    if method in (MethodChoice.embedding, MethodChoice.all):
        backend = embedding_backend_name()
        path = build_embedding_index()
        console.print(f"[green]Embedding index ({backend}):[/green] {path}")
    idx = get_index_stats()
    console.print(
        f"Indeks: geometric={idx['geometric_count']}, embedding={idx['embedding_count']}"
    )


@app.command("query")
def cmd_query(
    profile_id: str = typer.Option(..., "--profile-id", "-p"),
    method: MethodChoice = typer.Option(MethodChoice.embedding, "--method", "-m"),
    top_k: int = typer.Option(10, "--top-k", "-k"),
    json_output: bool = typer.Option(True, "--json/--table"),
) -> None:
    """Find top-k similar profiles."""
    if method == MethodChoice.all:
        raise typer.BadParameter("Choose geometric or embedding for query")

    sim_method = SimilarityMethod(method.value)
    results = query_similar(profile_id, sim_method, top_k=top_k)
    response = QueryResponse(
        query_profile_id=profile_id,
        method=sim_method,
        results=results,
    )

    if json_output:
        typer.echo(response.model_dump_json(indent=2))
    else:
        table = Table(title=f"Similar to {profile_id} ({sim_method.value})")
        table.add_column("Rank")
        table.add_column("Profile")
        table.add_column("Score")
        for r in results:
            table.add_row(str(r.rank), r.candidate_profile_id, f"{r.score:.4f}")
        console.print(table)


@app.command("ingest-extral")
def cmd_ingest_extral(
    json_path: Path = typer.Option(
        EXTRAL_JSON,
        exists=True,
        help="Ścieżka do matryce - dane v2.json",
    ),
    limit: int | None = typer.Option(None, help="Ogranicz liczbę profili (test)"),
    keep_existing: bool = typer.Option(False, "--keep-existing", help="Nie czyść bazy przed importem"),
) -> None:
    """Import profili i matryc z eksportu Extral JSON."""
    init_db()
    console.print(f"[cyan]Import z:[/cyan] {json_path}")
    stats = ingest_extral_json(json_path, limit=limit, clear_existing=not keep_existing)
    table = Table(title="Import Extral JSON")
    for k, v in stats.items():
        table.add_row(k, str(v))
    console.print(table)


@app.command("bootstrap-extral")
def cmd_bootstrap_extral(
    json_path: Path = typer.Option(EXTRAL_JSON, exists=True),
    limit: int | None = typer.Option(None, help="Ogranicz liczbę profili (test)"),
    skip_index: bool = typer.Option(False, help="Pomiń budowę indeksu (szybki import)"),
) -> None:
    """Pełny pipeline na danych klienta: import → normalizacja → indeks."""
    init_db()
    console.print("[bold]Matrix Advisor — bootstrap Extral[/bold]")
    stats = ingest_extral_json(json_path, limit=limit, clear_existing=True)
    console.print(f"Import: {stats}")
    nstats = normalize_all()
    console.print(f"Normalizacja: {nstats}")
    if not skip_index:
        build_geometric_index()
        backend = embedding_backend_name()
        build_embedding_index()
        console.print(f"[green]Indeks gotowy ({backend})[/green]")
    console.print("[green]Bootstrap zakończony.[/green] Uruchom: [bold]matrix-advisor dev[/bold]")


@app.command("process-dxf")
def cmd_process_dxf(
    profile_id: str = typer.Option(..., "--profile-id", "-p"),
    dxf_path: Path | None = typer.Option(None, exists=True, help="DXF file (default: data/raw/dxf/{id}.dxf)"),
) -> None:
    """Process a single profile DXF through the full pipeline."""
    from matrix_advisor.config import RAW_DXF

    init_db()
    path = dxf_path or (RAW_DXF / f"{profile_id}.dxf")
    if not path.exists():
        raise typer.BadParameter(f"DXF not found: {path}")
    result = process_dxf_file(path, persist=True)
    console.print(f"[green]Processed[/green] {profile_id} strategy={result.selection.strategy}")
    console.print(f"Dimensions: {result.dimensions_mapped}")
    if result.quality_flags:
        console.print(f"Flags: {result.quality_flags}")


@app.command("import-dxf")
def cmd_import_dxf(
    directory: Path = typer.Option(..., "--dir", exists=True, help="Folder with *.dxf files"),
) -> None:
    """Batch-import DXF files from a directory."""
    init_db()
    reports = import_dxf_directory(directory)
    table = Table(title=f"Import DXF from {directory}")
    table.add_column("File")
    table.add_column("Status")
    table.add_column("Strategy")
    table.add_column("Notes")
    for r in reports:
        notes = r.get("error") or ", ".join(r.get("quality_flags") or [])
        table.add_row(r["file"], r["status"], r.get("strategy", "—"), notes[:60])
    console.print(table)


@app.command("dev")
def cmd_dev(
    host: str = typer.Option("127.0.0.1"),
    api_port: int = typer.Option(8765),
    ui_port: int = typer.Option(5173),
) -> None:
    """Uruchom API + UI (jedna komenda)."""
    import subprocess
    import sys
    from pathlib import Path

    init_db()
    web_dir = Path(__file__).resolve().parents[2] / "web"
    if not (web_dir / "package.json").exists():
        console.print("[red]Brak katalogu web/. Uruchom npm install w tools/matrix-advisor-poc/web[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Matrix Advisor[/green] API :{api_port} + UI :{ui_port}")
    api_cmd = [
        sys.executable, "-m", "uvicorn",
        "matrix_advisor.api.server:app",
        "--host", host, "--port", str(api_port),
    ]
    ui_cmd = ["npm", "run", "dev", "--", "--port", str(ui_port), "--host"]
    proc_api = subprocess.Popen(api_cmd)
    try:
        subprocess.run(ui_cmd, cwd=web_dir, check=True)
    finally:
        proc_api.terminate()
        proc_api.wait()


@app.command("serve")
def cmd_serve(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8765, help="Bind port"),
) -> None:
    """Start HTTP API for cut-planner demo UI."""
    import uvicorn

    init_db()
    console.print(f"[green]Matrix Advisor API[/green] http://{host}:{port}/api/v1/health")
    uvicorn.run("matrix_advisor.api.server:app", host=host, port=port, reload=False)


@app.command("pipeline")
def cmd_pipeline(
    count: int = typer.Option(24, help="Sample profile count"),
    force: bool = typer.Option(False, "--force", help="Pozwól nadpisać indeks przy dużej bazie Extral"),
) -> None:
    """Run full PoC pipeline on synthetic sample data."""
    from matrix_advisor.query.service import get_stats

    stats = get_stats()
    if stats["profiles"] > 500 and not force:
        console.print(
            "[red]Baza zawiera dane Extral "
            f"({stats['profiles']} profili).[/red] "
            "Pipeline nadpisze indeks sample'ami.\n"
            "Użyj --force jeśli naprawdę chcesz sample, "
            "albo: matrix-advisor build-index --method all"
        )
        raise typer.Exit(1)
    init_db()
    generate_sample_data(count=count)
    ingest_profiles(SAMPLE_DIR / "profiles.csv", SAMPLE_DIR / "pictograms")
    ingest_matrices(SAMPLE_DIR / "matrices.csv")
    normalize_all()
    build_geometric_index()
    build_embedding_index()
    console.print("[green]Pipeline complete.[/green]")
    console.print("  Dev:  matrix-advisor dev")


if __name__ == "__main__":
    app()
