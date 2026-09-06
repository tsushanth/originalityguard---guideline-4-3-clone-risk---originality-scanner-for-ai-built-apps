# OriginalityGuard (local MVP)

A local, offline-friendly proof of concept for OriginalityGuard: a
pre-submission clone-risk scanner for iOS developers worried about Apple's
Guideline 4.3 crackdown on AI-generated/vibe-coded clone apps.

Given your app's title, subtitle, description, and feature bullets, it
runs a semantic-embedding similarity search against a catalog of existing
App Store apps and flags "too similar to existing app X" risk with a
score. It also demonstrates the post-launch "continuous monitoring" angle
by re-scanning and diffing against the last saved scan to surface
newly-appeared near-duplicates.

This is a CLI-only scaffold: no server, no accounts, no database. See
`plan.md` for the full scope and what's deliberately left out.

## How it works

- `src/embed.py` — loads a small local embedding model
  (`all-MiniLM-L6-v2` via `sentence-transformers`, runs fully offline
  after the first download) and computes cosine similarity.
- `src/scan.py` — embeds your app description and every catalog entry,
  ranks the catalog by similarity, and prints a "HIGH CLONE RISK" or "LOW
  risk" verdict.
- `src/monitor.py` — re-runs a scan and diffs the set of near-duplicates
  (score above threshold) against the last saved scan in
  `data/scan_history/`, printing an alert for any that are new.
- `src/fetch_catalog.py` — pulls a sample of real app metadata for a
  search term/category from Apple's public iTunes Search API (no key
  required) into `data/catalog_cache.json`.
- `data/catalog_seed.json` — a small committed sample catalog so the demo
  works with zero network access.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The first run of `scan.py` or `monitor.py` downloads the embedding model
(a few hundred MB) — after that everything runs offline.

## Try it

1. (Optional) Fetch a real sample catalog for a category:

   ```bash
   python src/fetch_catalog.py --term "habit tracker" --limit 50
   ```

   Or skip this and use the committed offline fallback,
   `data/catalog_seed.json`, in the commands below.

2. Look at `app_input/sample_app.json` — a fictitious habit-tracker app
   ("HabitFlare") whose description closely mirrors one entry in
   `data/catalog_seed.json` ("StreakForge"), on purpose, so the clone-risk
   detection has something obvious to catch. Edit it to describe your own
   app, or leave it as-is to see the demo fire.

3. Run a one-shot scan:

   ```bash
   python src/scan.py --input app_input/sample_app.json --catalog data/catalog_seed.json
   ```

   This prints a ranked similarity table and a verdict, e.g.:

   ```
   HIGH CLONE RISK: too similar to StreakForge (score 0.86)
   ```

   Add `--report out.md` to also save a markdown report.

4. Demonstrate continuous monitoring — run `monitor.py` once to establish
   a baseline, then again after the catalog changes to see a new
   near-duplicate get flagged:

   ```bash
   python src/monitor.py --input app_input/sample_app.json --catalog data/catalog_seed.json
   # -> "Baseline scan saved — recording N near-duplicate(s)."

   # now add a new near-duplicate entry to the catalog JSON (or re-fetch
   # a catalog that now includes a new competitor), then run again:
   python src/monitor.py --input app_input/sample_app.json --catalog data/catalog_seed.json
   # -> "NEW near-duplicate detected since last scan: <name>"
   ```

   Each run's ranked results are saved to `data/scan_history/`, which
   `monitor.py` uses to diff against the next run.

## Tests

```bash
pytest tests/
```

Tests cover the cosine-similarity math (`test_embed.py`) and the
ranking/threshold-flagging logic on a small fixture catalog
(`test_scan.py`). Both run fast and fully offline — they don't load the
real embedding model, only the pure math and ranking logic around it.

## Your app's input format

`app_input/sample_app.json` (and any file you pass to `--input`):

```json
{
  "name": "Your App Name",
  "subtitle": "Short subtitle",
  "description": "Full App Store description...",
  "features": ["Feature bullet one", "Feature bullet two"]
}
```
