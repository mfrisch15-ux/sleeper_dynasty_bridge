
import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

LEAGUE_ID = "1328462469961613312"
USERNAME = "mfrisch15"
BASE = "https://api.sleeper.app/v1"

def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent":"sleeper-dynasty-bridge/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

state = get("/state/nfl")
week = int(state.get("week") or 1)
league = get(f"/league/{LEAGUE_ID}")
users = get(f"/league/{LEAGUE_ID}/users")
rosters = get(f"/league/{LEAGUE_ID}/rosters")
matchups = get(f"/league/{LEAGUE_ID}/matchups/{week}")
traded_picks = get(f"/league/{LEAGUE_ID}/traded_picks")
players = get("/players/nfl")
me = get(f"/user/{USERNAME}")
my_uid = me.get("user_id")

user_by_id = {u.get("user_id"): u for u in users}
manager_rosters = []

for r in rosters:
    u = user_by_id.get(r.get("owner_id"), {})
    starters = {str(x) for x in (r.get("starters") or [])}
    reserve = {str(x) for x in (r.get("reserve") or [])}
    taxi = {str(x) for x in (r.get("taxi") or [])}
    resolved = []
    for pid in (r.get("players") or []):
        p = players.get(str(pid), {})
        resolved.append({
            "player_id": str(pid),
            "name": p.get("full_name") or " ".join(filter(None,[p.get("first_name"),p.get("last_name")])),
            "position": p.get("position"),
            "team": p.get("team"),
            "injury_status": p.get("injury_status"),
            "is_starter": str(pid) in starters,
            "is_reserve": str(pid) in reserve,
            "is_taxi": str(pid) in taxi,
        })
    manager_rosters.append({
        "roster_id": r.get("roster_id"),
        "owner_id": r.get("owner_id"),
        "display_name": u.get("display_name"),
        "team_name": (u.get("metadata") or {}).get("team_name"),
        "settings": r.get("settings"),
        "players": resolved,
    })

transactions = {}
for wk in range(max(1, week-3), week+1):
    try:
        transactions[str(wk)] = get(f"/league/{LEAGUE_ID}/transactions/{wk}")
    except Exception:
        transactions[str(wk)] = []

snapshot = {
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "league_id": LEAGUE_ID,
    "sleeper_username": USERNAME,
    "my_user_id": my_uid,
    "nfl_state": state,
    "league": league,
    "manager_rosters": manager_rosters,
    "matchups_current_week": matchups,
    "transactions_recent": transactions,
    "traded_picks": traded_picks,
}

out = Path("data/league_snapshot.json")
out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
print(out)
