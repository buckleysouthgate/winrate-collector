# winrate-collector
# Winrate Collector

Autonomous data collection for the Winrate venture. Pulls the GETS RSS feeds twice daily (all tenders, plus the MoE School Infrastructure feed), stores the raw XML forever, and appends newly seen tenders to CSVs. Runs entirely on GitHub's servers: no desktop, no cost on the free tier, roughly two polite requests per run against feeds that exist precisely for this purpose.

## Deploy from any browser (iPad works), about 15 minutes

1. Sign in at github.com and create a new PRIVATE repository named `winrate-collector`. Tick "Add a README" so the repo isn't empty, you'll replace it.
2. Open the repo, tap Add file, then Create new file. In the filename box type `.github/workflows/collect.yml` (the slashes create the folders). Paste the contents of collect.yml. Commit.
3. Add file again, name it `collect.py`, paste its contents. Commit.
4. Replace the README contents with this file if you want, or leave it.
5. Go to the Actions tab. If prompted, enable workflows for this repo.
6. Open "GETS daily collect" and tap "Run workflow" to trigger the first run manually. After a minute, a `data/` folder should appear containing raw XML and CSVs.

From then on it runs itself at 5:30am and 5:30pm UTC daily. Every run that finds new tenders commits them, so the repo becomes a timestamped ledger of every tender GETS publishes: the longitudinal dataset E1 actually wants, plus a growing pipeline feed no chat session has to re-fetch.

## Notes

- Raw XML is always saved before parsing, so a parser failure never loses data. Cowork can reprocess raw files later.
- To add feeds (per-agency GETS feeds, state portals when verified), edit the FEEDS dict in collect.py.
- Keep the repo private. The data is public, the venture's interest in it is not.
