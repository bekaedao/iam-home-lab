import csv
import os
import sys
from datetime import datetime, timezone
from graph_auth import GRAPH, get_all

DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30   # e.g. python 02_stale_accounts.py 7
now = datetime.now(timezone.utc)

users = get_all(f"{GRAPH}/users?$select=displayName,userPrincipalName,department,"
                f"accountEnabled,createdDateTime,signInActivity&$top=100")

rows = []
for u in users:
    last = (u.get("signInActivity") or {}).get("lastSignInDateTime")
    if last:
        days = (now - datetime.fromisoformat(last.replace("Z", "+00:00"))).days
        status = f"STALE ({days} days)" if days >= DAYS else "Active"
        last_txt = last[:10]
    else:
        days, status, last_txt = None, "NEVER SIGNED IN", "never"
    if not u.get("accountEnabled"):
        status = "Disabled"
    rows.append({"name": u["displayName"], "department": u.get("department") or "-",
                 "enabled": u.get("accountEnabled"), "last_sign_in": last_txt, "status": status})

order = {"N": 0, "S": 1, "A": 2, "D": 3}
rows.sort(key=lambda r: (order[r["status"][0]], r["name"]))

os.makedirs("output", exist_ok=True)
path = os.path.join("output", f"stale_accounts_{now:%Y-%m-%d}.csv")
with open(path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print(f"\nEDAO LOGISTICS - STALE ACCOUNT REPORT (threshold: {DAYS} days)\n")
print(f"{'Name':<24}{'Department':<13}{'Last sign-in':<15}{'Status'}")
print("-" * 70)
for r in rows:
    print(f"{r['name'][:23]:<24}{r['department'][:12]:<13}{r['last_sign_in']:<15}{r['status']}")

flagged = [r for r in rows if r["status"].startswith(("STALE", "NEVER"))]
print(f"\n{len(flagged)} enabled account(s) need review. Report saved to {path}")