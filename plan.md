# OriginalityGuard — Local MVP Scaffold Plan

## Goal

Prove the core value locally: given a description of *your* app (title,
subtitle, description, feature bullets), semantically compare it against a
catalog of existing App Store apps and surface "this looks too similar to
X" risk, with a score. Also demonstrate the "continuous monitoring" angle
by re-running the scan against a refreshed catalog and diffing for newly
appeared near-duplicates.

No deployed service, no app-store submission, no accounts. Everything
runs from the command line against local files.

## 1. Stack

**Python 3 CLI scripts** (no framework, no server):

- `sentence-transformers` (small local model, e.g. `all-MiniLM-L6-v2`) for
  text embeddings — runs fully offline after first model download, no API
  key, no billing. This is the load-bearing piece since "semantic
  embedding similarity" is the actual pitch, so it can't be swapped for
  plain keyword/TF-IDF matching without gutting the core value.
- `numpy` for cosine similarity math.
- `requests` + Apple's public **iTunes Search API** (`itunes.apple.com/search`,
  no auth/key required) to pull a real sample of existing app metadata by
  search term/category, cached to a local JSON file.
- Flat JSON files for storage (catalog cache, scan history). No database.
- `pytest` for tests.

Why Python over Node/Go here: `sentence-transformers` gives a
zero-infra, zero-API-key local embedding model, which is the cheapest way
to demo "semantic similarity" without standing up a vector DB or paying
for an embeddings API.

## 2. Explicitly scoped OUT

- **Auth / accounts / billing** — not needed to prove the matching logic
  works on local files.
- **Hosting / deploy / web UI** — CLI output (console table + optional
  markdown report file) is enough to show the verdict; no server needed.
- **Live full-catalog scraping** — scraping the entire App Store isn't
  needed to demo similarity search on a representative sample; the free
  iTunes Search API gives real metadata for a chosen search term/category
  without scraping HTML or hitting ToS/rate-limit concerns. A small
  committed static seed file (`catalog_seed.json`) is included as an
  offline fallback so the demo works with zero network access.
- **Screenshot / image visual similarity** — the idea description
  mentions screenshots, but text-embedding similarity on title +
  description + feature list is sufficient to prove the core "clone-risk"
  detection value. Image embeddings (CLIP etc.) are a real but separate
  feature and add real complexity — cut for the MVP.
- **Real-time/continuous background monitoring (daemon, cron, push
  alerts)** — the "continuous monitoring" value is demoed by letting the
  user manually re-run `monitor.py`, which diffs the new scan against the
  last saved scan and flags newly-appeared near-duplicates. No scheduler,
  no notification delivery (email/Slack/push) — a console alert is enough
  to prove the concept.
- **Apple policy-text tracking (detecting guideline 4.3 wording changes)**
  — out of scope; the MVP only does clone-similarity detection, not
  policy-diffing.
- **Persistent database / vector DB (Pinecone, pgvector, etc.)** — the
  catalog sample is small enough (tens to low hundreds of apps) that
  brute-force cosine similarity over an in-memory numpy array is
  instant; no indexing infra needed at this scale.

## 3. File / directory layout

```
originalityguard-mvp/
  data/
    catalog_seed.json       # small committed sample catalog (offline fallback)
    catalog_cache.json      # fetched from iTunes Search API (gitignored)
    scan_history/           # saved past scan results, used by monitor.py to diff
  app_input/
    sample_app.json         # example "your app" description to scan
  src/
    fetch_catalog.py        # pulls sample metadata from iTunes Search API
    embed.py                # shared: load model, embed text, cosine similarity
    scan.py                 # one-shot: compare app_input against catalog, print/save report
    monitor.py              # re-run scan, diff against last saved scan, flag new near-duplicates
    report.py               # formats console table + optional markdown report
  tests/
    test_embed.py           # cosine similarity math on known vectors
    test_scan.py            # ranking + threshold-flagging logic on a small fixture catalog
  requirements.txt
```

## 4. Verification

**Automated:**
- `pytest tests/` — covers:
  - `test_embed.py`: cosine similarity returns expected ordering/values
    for fixed, hand-checked vectors.
  - `test_scan.py`: given a tiny fixture catalog containing one obvious
    near-duplicate and several unrelated apps, `scan.py`'s ranking logic
    puts the duplicate on top and marks it above the risk threshold,
    while unrelated apps stay below it.

**Manual run-through:**
1. `pip install -r requirements.txt`
2. `python src/fetch_catalog.py --term "habit tracker" --limit 50`
   (or skip and rely on the committed `catalog_seed.json` if offline) →
   populates `data/catalog_cache.json`.
3. Edit `app_input/sample_app.json` to describe a fictitious app that
   closely resembles a well-known existing app (e.g. a habit tracker with
   near-identical feature bullets).
4. `python src/scan.py --input app_input/sample_app.json --catalog data/catalog_cache.json`
   → prints a ranked similarity table and a clear "HIGH CLONE RISK: too
   similar to <App Name> (score 0.xx)" verdict.
5. Add one more fake near-duplicate entry to the cached catalog, then run
   `python src/monitor.py --input app_input/sample_app.json --catalog data/catalog_cache.json`
   twice — the first run establishes a baseline in `data/scan_history/`,
   the second should print "NEW near-duplicate detected since last scan:
   <name>" for the added entry, proving the post-launch monitoring diff
   logic.
