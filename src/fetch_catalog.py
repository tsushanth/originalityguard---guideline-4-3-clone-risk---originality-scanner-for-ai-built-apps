"""Pull a sample of real app metadata from Apple's public iTunes Search API.

No auth/key required. Results are normalized to the same shape as
data/catalog_seed.json so scan.py and monitor.py can use either
interchangeably.
"""

import argparse
import json
import sys
from pathlib import Path

import requests

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
DEFAULT_OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "catalog_cache.json"


def fetch(term, limit=50, country="us"):
    params = {"term": term, "entity": "software", "limit": limit, "country": country}
    resp = requests.get(ITUNES_SEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return [
        {
            "id": r.get("trackId"),
            "name": r.get("trackName"),
            "subtitle": "",
            "description": r.get("description", ""),
            "genre": r.get("primaryGenreName", ""),
            "url": r.get("trackViewUrl", ""),
        }
        for r in results
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Fetch a sample app catalog from the iTunes Search API."
    )
    parser.add_argument("--term", required=True, help="Search term / category, e.g. 'habit tracker'")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--country", default="us")
    parser.add_argument("--out", default=str(DEFAULT_OUT_PATH))
    args = parser.parse_args()

    try:
        catalog = fetch(args.term, args.limit, args.country)
    except requests.RequestException as exc:
        print(f"Failed to fetch from iTunes Search API: {exc}", file=sys.stderr)
        print(
            "No network access? Use the offline fallback instead: "
            "--catalog data/catalog_seed.json",
            file=sys.stderr,
        )
        sys.exit(1)

    if not catalog:
        print("No results returned for that term.", file=sys.stderr)
        sys.exit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(catalog, f, indent=2)
    print(f"Saved {len(catalog)} apps to {out_path}")


if __name__ == "__main__":
    main()
