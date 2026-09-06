"""One-shot scan: compare app_input against a catalog, print/save a report."""

import argparse
import json

from embed import cosine_similarity, embed_texts
from report import format_table, save_markdown_report

DEFAULT_THRESHOLD = 0.6


def app_to_text(app):
    parts = [app.get("name", ""), app.get("subtitle", ""), app.get("description", "")]
    parts.extend(app.get("features", []))
    return " ".join(p for p in parts if p)


def catalog_entry_to_text(entry):
    parts = [entry.get("name", ""), entry.get("subtitle", ""), entry.get("description", "")]
    return " ".join(p for p in parts if p)


def rank_catalog(app, catalog, embed_fn=embed_texts):
    """Embed the app + every catalog entry, return catalog ranked by similarity desc."""
    query_text = app_to_text(app)
    corpus_texts = [catalog_entry_to_text(entry) for entry in catalog]
    vectors = embed_fn([query_text] + corpus_texts)
    query_vec, corpus_vecs = vectors[0], vectors[1:]

    scored = [
        {
            "id": entry.get("id"),
            "name": entry.get("name"),
            "score": cosine_similarity(query_vec, vec),
        }
        for entry, vec in zip(catalog, corpus_vecs)
    ]
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored


def verdict(ranked, threshold=DEFAULT_THRESHOLD):
    if not ranked:
        return "No catalog entries to compare against."
    top = ranked[0]
    if top["score"] >= threshold:
        return f"HIGH CLONE RISK: too similar to {top['name']} (score {top['score']:.2f})"
    return (
        f"LOW risk: closest match is {top['name']} "
        f"(score {top['score']:.2f}), below threshold {threshold:.2f}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Scan an app description against a catalog for Guideline 4.3 clone-risk."
    )
    parser.add_argument("--input", required=True, help="Path to your app's JSON description")
    parser.add_argument("--catalog", required=True, help="Path to a catalog JSON file")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--report", help="Optional path to save a markdown report")
    args = parser.parse_args()

    with open(args.input) as f:
        app = json.load(f)
    with open(args.catalog) as f:
        catalog = json.load(f)

    ranked = rank_catalog(app, catalog)
    verdict_text = verdict(ranked, args.threshold)

    print(format_table(ranked))
    print()
    print(verdict_text)

    if args.report:
        save_markdown_report(ranked, verdict_text, args.report)
        print(f"\nReport saved to {args.report}")


if __name__ == "__main__":
    main()
