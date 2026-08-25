# Sleeper Dynasty League Bridge

League ID: `1328462469961613312`
Sleeper username: `mfrisch15`

This repo refreshes a JSON snapshot of the league from Sleeper's public read-only API.

## Setup
1. Create a public GitHub repo.
2. Upload these files to the repo root.
3. Enable GitHub Actions.
4. Run **Refresh Sleeper League Snapshot** once.
5. Share this URL with ChatGPT:

`https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/<REPO_NAME>/main/data/league_snapshot.json`

The workflow refreshes the snapshot every 6 hours.
