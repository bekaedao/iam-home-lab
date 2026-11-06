import csv
import os
from datetime import datetime
from graph_auth import GRAPH, get_all

data = get_all(f"{GRAPH}/reports/authenticationMethods/userRegistrationDetails")

rows = []
for d in data:
    methods = ", ".join(d.get("methodsRegistered") or []) or "none"
    mfa = d.get("isMfaRegistered")
    admin = d.get("isAdmin")
    if not mfa and admin:
        risk = "HIGH - admin without MFA"
    elif not mfa:
        risk = "MEDIUM - no MFA"
    else:
        risk = "OK"
    rows.append({"name": d.get("userDisplayName"), "admin": admin, "mfa_registered": mfa,
                 "methods": methods, "risk": risk})

rows.sort(key=lambda r: ({"H": 0, "M": 1, "O": 2}[r["risk"][0]], r["name"] or ""))

os.makedirs("output", exist_ok=True)
path = os.path.join("output", f"mfa_report_{datetime.now():%Y-%m-%d}.csv")
with open(path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print(f"\nEDAO LOGISTICS - MFA REGISTRATION REPORT ({datetime.now():%Y-%m-%d})\n")
print(f"{'Name':<24}{'Admin':<8}{'MFA':<8}{'Risk':<27}{'Methods'}")
print("-" * 100)
for r in rows:
    print(f"{(r['name'] or '')[:23]:<24}{str(r['admin']):<8}{str(r['mfa_registered']):<8}"
          f"{r['risk']:<27}{r['methods'][:40]}")

registered = sum(1 for r in rows if r["mfa_registered"])
print(f"\nMFA coverage: {registered} of {len(rows)} users ({registered * 100 // len(rows)}%). "
      f"Report saved to {path}")