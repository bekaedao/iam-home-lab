import csv
import os
import sys
from datetime import datetime
import requests
from graph_auth import GRAPH, headers, check

if len(sys.argv) < 2:
    raise SystemExit('Usage: python 05_leaver.py "Full Name"')
name = sys.argv[1]
h = headers()

found = check(requests.get(f"{GRAPH}/users?$filter=displayName eq '{name}'"
                           f"&$select=id,displayName,department,accountEnabled",
                           headers=h, timeout=30)).json()["value"]
if len(found) != 1:
    raise SystemExit(f"Expected exactly 1 user named '{name}', found {len(found)}. Nothing changed.")
user = found[0]
uid = user["id"]

groups = check(requests.get(f"{GRAPH}/users/{uid}/memberOf/microsoft.graph.group"
                            f"?$select=id,displayName,groupTypes",
                            headers=h, timeout=30)).json()["value"]

print(f"\nLEAVER: {user['displayName']} ({user.get('department') or '-'})")
print(f"Groups: {', '.join(g['displayName'] for g in groups) or 'none'}")
if input("Type YES to offboard this user: ").strip() != "YES":
    raise SystemExit("Cancelled. Nothing changed.")

log = []
def record(action, detail):
    print(f"[+] {action}: {detail}")
    log.append({"time": datetime.now().isoformat(timespec="seconds"), "action": f"LEAVER - {action}",
                "user": user["displayName"], "department": user.get("department") or "-", "group": detail})

check(requests.patch(f"{GRAPH}/users/{uid}", headers=h, json={"accountEnabled": False}, timeout=30))
record("Account disabled", "accountEnabled = false")

check(requests.post(f"{GRAPH}/users/{uid}/revokeSignInSessions", headers=h, timeout=30))
record("Sessions revoked", "all refresh tokens invalidated")

for g in groups:
    if "DynamicMembership" in (g.get("groupTypes") or []):
        record("Skipped dynamic group", f"{g['displayName']} (membership is rule-based)")
        continue
    check(requests.delete(f"{GRAPH}/groups/{g['id']}/members/{uid}/$ref", headers=h, timeout=30))
    record("Removed from group", g["displayName"])

os.makedirs("output", exist_ok=True)
path = os.path.join("output", "lifecycle_log.csv")
new = not os.path.exists(path)
with open(path, "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=log[0].keys())
    if new:
        w.writeheader()
    w.writerows(log)
print(f"\nOffboarding complete. {len(log)} actions logged to {path}")