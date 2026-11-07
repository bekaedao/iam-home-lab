import csv
import os
from graph_auth import GRAPH, get_all

os.makedirs("data", exist_ok=True)

def write(name, rows, fields):
    with open(os.path.join("data", name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"[+] {name}: {len(rows)} rows")

# 1. Users, including last sign-in
users = get_all(f"{GRAPH}/users?$select=id,displayName,userPrincipalName,givenName,surname,"
                f"department,jobTitle,accountEnabled,userType,createdDateTime,signInActivity&$top=100")
write("users.csv", [{
    "user_id": u["id"], "display_name": u["displayName"], "upn": u["userPrincipalName"],
    "given_name": u.get("givenName") or "", "surname": u.get("surname") or "",
    "department": u.get("department") or "", "job_title": u.get("jobTitle") or "",
    "account_enabled": u.get("accountEnabled"), "user_type": u.get("userType"),
    "created": (u.get("createdDateTime") or "")[:10],
    "last_sign_in": ((u.get("signInActivity") or {}).get("lastSignInDateTime") or "")[:10],
} for u in users], ["user_id", "display_name", "upn", "given_name", "surname", "department",
                    "job_title", "account_enabled", "user_type", "created", "last_sign_in"])

# 2. Group memberships (users only)
rows = []
for g in get_all(f"{GRAPH}/groups?$select=id,displayName,groupTypes&$top=100"):
    kind = "Dynamic" if "DynamicMembership" in (g.get("groupTypes") or []) else "Assigned"
    for m in get_all(f"{GRAPH}/groups/{g['id']}/members?$select=id,displayName"):
        if m.get("@odata.type") == "#microsoft.graph.user":
            rows.append({"user_id": m["id"], "display_name": m.get("displayName"),
                         "group_name": g["displayName"], "membership_type": kind})
write("group_memberships.csv", rows, ["user_id", "display_name", "group_name", "membership_type"])

# 3. MFA registration
write("mfa.csv", [{
    "user_id": d["id"], "display_name": d.get("userDisplayName"), "is_admin": d.get("isAdmin"),
    "mfa_registered": d.get("isMfaRegistered"), "methods": ", ".join(d.get("methodsRegistered") or []),
} for d in get_all(f"{GRAPH}/reports/authenticationMethods/userRegistrationDetails")],
    ["user_id", "display_name", "is_admin", "mfa_registered", "methods"])

# 4. Admin roles: active assignments + PIM-eligible assignments
names = {r["id"]: r["displayName"] for r in
         get_all(f"{GRAPH}/roleManagement/directory/roleDefinitions?$select=id,displayName")}
roles = [{"user_id": a["principalId"], "role": names.get(a["roleDefinitionId"], a["roleDefinitionId"]),
          "assignment": "Active"} for a in get_all(f"{GRAPH}/roleManagement/directory/roleAssignments")]
roles += [{"user_id": a["principalId"], "role": names.get(a["roleDefinitionId"], a["roleDefinitionId"]),
           "assignment": "Eligible (PIM)"}
          for a in get_all(f"{GRAPH}/roleManagement/directory/roleEligibilitySchedules")]
write("role_assignments.csv", roles, ["user_id", "role", "assignment"])

print("\nExport complete. Files are in the data folder.")