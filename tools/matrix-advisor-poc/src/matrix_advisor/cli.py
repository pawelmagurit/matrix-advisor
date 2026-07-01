import json
from enum import Enum
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from matrix_advisor.config import DATA_ROOT, EXTRAL_JSON, RAW_DXF, ensure_data_dirs
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
from matrix_advisor.models import QueryResponse, SimilarityMethod
from matrix_advisor.dxf.pipeline import import_dxf_directory, process_dxf_file
from matrix_advisor.index.builder import update_index_rows
from matrix_advisor.normalization.pipeline import normalize_all, repair_masks

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


@app.command("repair-masks")
def cmd_repair_masks(
    iou_threshold: float = typer.Option(
        0.9, help="Regeneruj maskę gdy IoU ze wzorcowym piktogramem < próg"
    ),
    skip_index: bool = typer.Option(False, help="Pomiń aktualizację indeksu"),
) -> None:
    """Napraw zdegenerowane maski (nadpisane przez import DXF) z piktogramów."""
    init_db()
    repaired = repair_masks(iou_threshold=iou_threshold)
    console.print(f"[green]Naprawiono masek:[/green] {len(repaired)}")
    if repaired:
        console.print(", ".join(repaired[:50]) + (" …" if len(repaired) > 50 else ""))
    if repaired and not skip_index:
        stats = update_index_rows(repaired)
        console.print(f"[green]Zaktualizowano indeks:[/green] {stats}")


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


@app.command("eval-dxf")
def cmd_eval_dxf(
    directory: Path = typer.Option(RAW_DXF, "--dir", exists=True, help="Folder z plikami *.dxf"),
    top_k: int = typer.Option(50, "--top-k", "-k", help="Głębokość rankingu dla self-retrieval"),
    out: Path = typer.Option(DATA_ROOT / "reports" / "dxf_eval.json", "--out", help="Zapisz pełny raport JSON"),
) -> None:
    """Oceń jakość ekstrakcji DXF→maska względem piktogramu (fallback wyłączony).

    Piktogram = ground truth. Mierzy IoU(maska z DXF, piktogram) oraz pozycję,
    na której zapytanie samą maską z DXF odzyskuje własny piktogram z indeksu.
    """
    from matrix_advisor.eval.dxf_pictogram_eval import evaluate_dxf_directory

    init_db()
    report = evaluate_dxf_directory(directory, top_k=top_k, out_path=out)
    s = report["summary"]
    console.print(
        f"[bold]Eval DXF→piktogram[/bold]  plików={s['total_files']} "
        f"ocenionych={s['evaluated']} błędów={s['errors']} bez_piktogramu={s['no_pictogram']}"
    )
    console.print(f"IoU: średnia={s['iou_mean']} mediana={s['iou_median']}  kubełki={s['iou_buckets']}")
    console.print(
        f"Self-retrieval: @1={s['retrieval_at_1_pct']}%  @5={s['retrieval_at_5_pct']}%  "
        f"@10={s['retrieval_at_10_pct']}%  poza_top{top_k}={s['not_retrieved_pct']}%"
    )
    tbl = Table(title="Per-file")
    for col in ("Profile", "Strategy", "IoU", "Bucket", "SelfRank", "Top1", "Flags"):
        tbl.add_column(col)
    for r in report["rows"]:
        tbl.add_row(
            r["profile_id"],
            str(r.get("strategy") or "—"),
            str(r.get("iou") if r.get("iou") is not None else r["status"]),
            str(r.get("iou_bucket") or "—"),
            str(r.get("self_rank") if r.get("self_rank") is not None else "—"),
            str(r.get("top1_id") or "—"),
            ", ".join(r.get("quality_flags") or [])[:40],
        )
    console.print(tbl)
    if report["rows"]:
        by_strat = s["by_strategy"]
        st = Table(title="Per-strategy")
        for col in ("Strategy", "N", "IoU mean", "Retr@1 %"):
            st.add_column(col)
        for name, b in sorted(by_strat.items(), key=lambda kv: -kv[1]["count"]):
            st.add_row(name, str(b["count"]), str(b["iou_mean"]), str(b["retr_at1_pct"]))
        console.print(st)
    if out:
        console.print(f"[green]Raport:[/green] {out}")


@app.command("select-dxf-sample")
def cmd_select_dxf_sample(
    n: int = typer.Option(400, "--n", help="Docelowa liczność próbki do poproszenia"),
    out: Path = typer.Option(DATA_ROOT / "reports" / "dxf_sample_request.csv", "--out"),
    include_existing: bool = typer.Option(
        False, "--include-existing", help="Nie wykluczaj profili, dla których już mamy DXF"
    ),
    min_per_stratum: int = typer.Option(
        1, "--min-per-stratum", help="Min. reprezentantów na wartość każdej fasety metadanych"
    ),
) -> None:
    """Wygeneruj reprezentatywną (nie losową) listę indeksów, których DXF poprosić."""
    from matrix_advisor.eval.sample_selector import select_sample, write_sample_csv

    init_db()
    result = select_sample(
        n=n,
        exclude_existing_dxf=not include_existing,
        min_per_stratum=min_per_stratum,
    )
    write_sample_csv(result, out)
    cov = result.coverage
    console.print(
        f"[bold]Próbka DXF do poproszenia[/bold] — wybrano {cov['selected']} "
        f"(cel {cov['requested_n']})"
    )
    for facet, info in cov["facets"].items():
        console.print(
            f"  {facet}: pokryto {info['values_covered']}/{info['values_total']} wartości  "
            f"{info['distribution']}"
        )
    console.print(f"[green]Lista CSV:[/green] {out}")


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


if __name__ == "__main__":
    app()
