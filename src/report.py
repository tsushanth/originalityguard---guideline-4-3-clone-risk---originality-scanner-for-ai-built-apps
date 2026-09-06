"""Console table + markdown report formatting for scan results."""

from pathlib import Path


def format_table(ranked, limit=10):
    rows = ranked[:limit]
    header = f"{'Rank':<5}{'Score':<8}{'App Name'}"
    lines = [header, "-" * max(len(header), 30)]
    for i, r in enumerate(rows, start=1):
        lines.append(f"{i:<5}{r['score']:.2f}    {r['name']}")
    return "\n".join(lines)


def save_markdown_report(ranked, verdict_text, path, limit=10):
    rows = ranked[:limit]
    lines = [
        "# OriginalityGuard Scan Report",
        "",
        verdict_text,
        "",
        "| Rank | Score | App Name |",
        "|---|---|---|",
    ]
    for i, r in enumerate(rows, start=1):
        lines.append(f"| {i} | {r['score']:.2f} | {r['name']} |")
    Path(path).write_text("\n".join(lines) + "\n")
