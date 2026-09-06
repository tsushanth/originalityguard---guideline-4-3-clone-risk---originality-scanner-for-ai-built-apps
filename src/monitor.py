"""Re-run a scan, diff against the last saved scan, flag newly-appeared near-duplicates.

Demonstrates the post-launch "continuous monitoring" angle without any
scheduler or notification delivery: run this script by hand whenever you
want to re-check the catalog.
"""

import argparse
import json
from pathlib import Path

from report import format_table
from scan import DEFAULT_THRESHOLD, rank_catalog, verdict

HISTORY_DIR = Path(__file__).resolve().parent.parent / "data" / "scan_history"


def load_latest_history():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(HISTORY_DIR.glob("scan_*.json"))
    if not files:
        return None
    with open(files[-1]) as f:
        return json.load(f)


def save_history(ranked, threshold):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(HISTORY_DIR.glob("scan_*.json"))
    next_n = len(existing) + 1
    near_duplicate_ids = [r["id"] for r in ranked if r["score"] >= threshold]
    payload = {"ranked": ranked, "threshold": threshold, "near_duplicate_ids": near_duplicate_ids}
    path = HISTORY_DIR / f"scan_{next_n:03d}.json"
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Re-scan and diff against the last saved scan for new near-duplicates."
    )
    parser.add_argument("--input", required=True, help="Path to your app's JSON description")
    parser.add_argument("--catalog", required=True, help="Path to a catalog JSON file")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()

    with open(args.input) as f:
        app = json.load(f)
    with open(args.catalog) as f:
        catalog = json.load(f)

    ranked = rank_catalog(app, catalog)
    print(format_table(ranked))
    print()
    print(verdict(ranked, args.threshold))

    previous = load_latest_history()
    current_near_dup_ids = {r["id"] for r in ranked if r["score"] >= args.threshold}

    if previous is None:
        print(f"\nBaseline scan saved — recording {len(current_near_dup_ids)} near-duplicate(s).")
    else:
        previous_ids = set(previous.get("near_duplicate_ids", []))
        new_ids = current_near_dup_ids - previous_ids
        if new_ids:
            id_to_name = {r["id"]: r["name"] for r in ranked}
            for new_id in new_ids:
                print(f"\nNEW near-duplicate detected since last scan: {id_to_name.get(new_id, new_id)}")
        else:
            print("\nNo new near-duplicates since last scan.")

    saved_path = save_history(ranked, args.threshold)
    print(f"\nScan saved to {saved_path}")


if __name__ == "__main__":
    main()
