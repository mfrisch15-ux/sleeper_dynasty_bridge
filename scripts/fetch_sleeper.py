import json, urllib.request
from datetime import datetime, timezone
from pathlib import Path

LEAGUE_ID = "1328462469961613312"
USERNAME = "mfrisch15"
BASE = "https://api.sleeper.app/v1"

def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent":"sleeper-dynasty-bridge/1.1"})
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
rostered_player_ids = set()

for r in rosters:
    u = user_by_id.get(r.get("owner_id"), {})
    player_ids = [str(x) for x in (r.get("players") or [])]
    rostered_player_ids.update(player_ids)
    starters = {str(x) for x in (r.get("starters") or [])}
    reserve = {str(x) for x in (r.get("reserve") or [])}
    taxi = {str(x) for x in (r.get("taxi") or [])}
    resolved = []
    for pid in player_ids:
        p = players.get(pid, {})
        resolved.append({
            "player_id": pid,
            "name": p.get("full_name") or " ".join(filter(None,[p.get("first_name"),p.get("last_name")])),
            "position": p.get("position"),
            "team": p.get("team"),
            "status": p.get("status"),
            "injury_status": p.get("injury_status"),
            "search_rank": p.get("search_rank"),
            "years_exp": p.get("years_exp"),
            "is_starter": pid in starters,
            "is_reserve": pid in reserve,
            "is_taxi": pid in taxi,
        })
    manager_rosters.append({
        "roster_id": r.get("roster_id"),
        "owner_id": r.get("owner_id"),
        "display_name": u.get("display_name"),
        "team_name": (u.get("metadata") or {}).get("team_name"),
        "settings": r.get("settings"),
        "players": resolved,
    })

free_agents = []
for pid, p in players.items():
    pid = str(pid)
    if pid in rostered_player_ids:
        continue
    position = p.get("position")
    team = p.get("team")
    status = (p.get("status") or "").lower()
    if position not in {"QB","RB","WR","TE"}:
        continue
    if not team or status in {"inactive","retired"}:
        continue
    rank = p.get("search_rank")
    if rank is None:
        rank = 999999
    free_agents.append({
        "player_id": pid,
        "name": p.get("full_name") or " ".join(filter(None,[p.get("first_name"),p.get("last_name")])),
        "position": position,
        "team": team,
        "status": p.get("status"),
        "injury_status": p.get("injury_status"),
        "search_rank": rank,
        "years_exp": p.get("years_exp"),
        "depth_chart_position": p.get("depth_chart_position"),
    })

free_agents.sort(key=lambda x:(x["search_rank"], x["position"], x["name"] or ""))
free_agent_pool_compact = free_agents[:150]
free_agents_by_position = {
    pos: [p for p in free_agent_pool_compact if p["position"] == pos][:40]
    for pos in ["QB","RB","WR","TE"]
}

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
    "free_agent_pool_compact": free_agent_pool_compact,
    "free_agents_by_position": free_agents_by_position,
    "free_agent_pool_metadata": {
        "included_positions": ["QB","RB","WR","TE"],
        "max_players": 150,
        "sort": "Sleeper search_rank ascending",
        "excludes_rostered_players": True,
        "excludes_players_without_current_team": True
    }
}

out = Path("data/league_snapshot.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
print(f"Wrote {out}")
