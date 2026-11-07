import csv
import glob
import os
import re
import sqlite3
from datetime import datetime

DB = "governance.db"
if os.path.exists(DB):
    os.remove(DB)                      # rebuild from the latest export every run
con = sqlite3.connect(DB)

def load(path, table):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cols = list(rows[0].keys())
    con.execute(f"CREATE TABLE {table} ({', '.join(c + ' TEXT' for c in cols)})")
    con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(cols))})",
                    [tuple(r[c] for c in cols) for r in rows])
    print(f"[load] {table:<18} {len(rows)} rows")

for p in sorted(glob.glob("data/*.csv")):
    load(p, os.path.splitext(os.path.basename(p))[0])
load("hr_roster.csv", "hr")
load("sod_rules.csv", "sod_rules")
con.commit()

scan_time = datetime.now().strftime("%Y-%m-%d %H:%M")
os.makedirs("findings", exist_ok=True)
all_rows = []

print(f"\nEDAO LOGISTICS - IDENTITY GOVERNANCE SCAN ({scan_time})\n")
blocks = re.split(r"^-- name: ", open("findings.sql", encoding="utf-8").read(), flags=re.M)[1:]
for block in blocks:
    title, query = block.split("\n", 1)
    code, name = title.strip().split(" ", 1)
    cur = con.execute(query)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    with open(f"findings/{code}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    print(f"{code}  {name}: {len(rows)}")
    for r in rows:
        detail = "; ".join(f"{k}={v}" for k, v in r.items() if k not in ("display_name", "risk"))
        print(f"      - {r['display_name']:<20} [{r['risk']}]  {detail}")
        all_rows.append({"scan_time": scan_time, "finding_id": code, "finding": name,
                         "user": r["display_name"], "risk": r["risk"], "detail": detail})

def one(sql):
    return con.execute(sql).fetchone()[0]

summary = {
    "scan_time": scan_time,
    "total_accounts": one("SELECT COUNT(*) FROM users"),
    "enabled_accounts": one("SELECT COUNT(*) FROM users WHERE account_enabled = 'True'"),
    "mfa_coverage_pct": one("SELECT ROUND(100.0 * SUM(mfa_registered = 'True') / COUNT(*)) FROM mfa"),
    "total_findings": len(all_rows),
    "high": sum(r["risk"] == "High" for r in all_rows),
    "medium": sum(r["risk"] == "Medium" for r in all_rows),
    "low": sum(r["risk"] == "Low" for r in all_rows),
}

def save(path, rows, append=False):
    new = not (append and os.path.exists(path))
    with open(path, "a" if append else "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        if new:
            w.writeheader()
        w.writerows(rows)

if all_rows:
    save("findings/all_findings.csv", all_rows)
    save("findings/findings_history.csv", all_rows, append=True)   # every scan, for before/after
save("findings/summary_history.csv", [summary], append=True)

print(f"\nSUMMARY: {summary['total_findings']} findings  |  High {summary['high']}  "
      f"Medium {summary['medium']}  Low {summary['low']}  |  MFA coverage {summary['mfa_coverage_pct']:.0f}%")
print("Results saved to the findings folder.")