import csv
import os
from datetime import datetime
from graph_auth import GRAPH, get_all

FIELDS = ["displayName", "userPrincipalName", "givenName", "surname",
          "department", "jobTitle", "accountEnabled", "createdDateTime"]

users = get_all(f"{GRAPH}/users?$select={','.join(FIELDS)}&$top=100")
users.sort(key=lambda u: (u.get("department") or "~", u.get("displayName") or ""))

os.makedirs("output", exist_ok=True)
path = os.path.join("output", f"user_inventory_{datetime.now():%Y-%m-%d}.csv")
with open(path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
    w.writeheader()
    w.writerows(users)

print(f"\nEDAO LOGISTICS - USER INVENTORY ({datetime.now():%Y-%m-%d %H:%M})\n")
print(f"{'Name':<24}{'Department':<14}{'Job title':<26}{'Enabled'}")
print("-" * 72)
for u in users:
    print(f"{(u.get('displayName') or '')[:23]:<24}"
          f"{(u.get('department') or '-')[:13]:<14}"
          f"{(u.get('jobTitle') or '-')[:25]:<26}"
          f"{u.get('accountEnabled')}")

disabled = [u["displayName"] for u in users if u.get("accountEnabled") is False]
print(f"\n{len(users)} users exported to {path}")
print(f"Disabled accounts: {len(disabled)} {disabled}")