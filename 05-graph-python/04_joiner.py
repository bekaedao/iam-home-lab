import csv
import os
import secrets
import string
from datetime import datetime
import requests
from graph_auth import GRAPH, headers, check, get_all

h = headers()

# Use the same domain as existing users (skip guest accounts)
domain = next(u["userPrincipalName"].split("@")[1]
              for u in get_all(f"{GRAPH}/users?$select=userPrincipalName")
              if "#EXT#" not in u["userPrincipalName"])

def temp_password():
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "Tmp-" + "".join(secrets.choice(chars) for _ in range(16))

def find_group(name):
    r = check(requests.get(f"{GRAPH}/groups?$filter=displayName eq '{name}'&$select=id,displayName",
                           headers=h, timeout=30)).json()["value"]
    return r[0] if r else None

log = []
with open("new_hires.csv", newline="", encoding="utf-8") as f:
    for hire in csv.DictReader(f):
        first, last = hire["givenName"].strip(), hire["surname"].strip()
        nick = f"{first}.{last}".lower()
        upn = f"{nick}@{domain}"

        body = {
            "accountEnabled": True,
            "displayName": f"{first} {last}",
            "givenName": first,          # required by SCIM / AWS (Lab 4 lesson)
            "surname": last,
            "mailNickname": nick,
            "userPrincipalName": upn,
            "department": hire["department"],
            "jobTitle": hire["jobTitle"],
            "usageLocation": "US",
            "passwordProfile": {"password": temp_password(), "forceChangePasswordNextSignIn": True},
        }
        user = check(requests.post(f"{GRAPH}/users", headers=h, json=body, timeout=30)).json()
        print(f"[+] Created {first} {last} ({hire['department']}, {hire['jobTitle']})")

        group_name = f"SG-{hire['department']}"
        group = find_group(group_name)
        if group:
            ref = {"@odata.id": f"{GRAPH}/directoryObjects/{user['id']}"}
            check(requests.post(f"{GRAPH}/groups/{group['id']}/members/$ref",
                                headers=h, json=ref, timeout=30))
            print(f"[+] Added to {group_name}")
        else:
            print(f"[!] Group {group_name} not found - no access granted")

        log.append({"time": datetime.now().isoformat(timespec="seconds"), "action": "JOINER",
                    "user": f"{first} {last}", "department": hire["department"],
                    "group": group_name if group else "none"})

os.makedirs("output", exist_ok=True)
path = os.path.join("output", "lifecycle_log.csv")
new = not os.path.exists(path)
with open(path, "a", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=log[0].keys())
    if new:
        w.writeheader()
    w.writerows(log)
print(f"\nDone. {len(log)} joiner(s) processed. Logged to {path}")
print("Temporary password was generated securely and never displayed or saved.")