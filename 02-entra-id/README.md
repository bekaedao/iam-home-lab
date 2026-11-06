# Lab 2: Microsoft Entra ID – Zero Trust Access

## Business problem

Edao Logistics (a fictional company) had no access rules, no enforced MFA, and admins who would hold full control permanently. A stolen admin password would mean a full tenant compromise.

## What I built

- A dedicated cloud admin account with MFA, plus an emergency **break-glass** account
- 8 employees across 4 departments, with department security groups for **role-based access control (RBAC)**
- A **dynamic group** that automatically adds anyone whose department is Finance
- Microsoft Entra ID **P2** licensing for all employees
- 3 **Conditional Access** policies, built and validated in report-only mode
- **Privileged Identity Management (PIM)**: User Administrator is *eligible* only, with justification, approval and a 2-hour time limit
- A quarterly **access review** on `SG-Finance` that caught and automatically removed a transferred employee's leftover access

| Tool | Used for |
| --- | --- |
| Microsoft Entra admin center | Users, groups, roles, Conditional Access, PIM |
| Microsoft 365 admin center | P2 license assignment |
| Microsoft Authenticator | MFA for admin and test users |

---

## Steps

### 1. Tenant and admin accounts

Renamed the tenant to Edao Logistics.

![Tenant properties](screenshots/lab2-01-tenant-overview.png)

Created a dedicated admin (Beka Admin) and a break-glass account (Emergency Access 01). Both hold Global Administrator. The break-glass account has a long, separately stored password and is excluded from every Conditional Access policy, so a bad rule can never lock the tenant.

![Break-glass account](screenshots/lab2-02a-breakglass-account.png)
![Global Administrator assignments](screenshots/lab2-02-global-admins.png)

### 2. Users and RBAC groups

Created 8 employees with department and job title filled in (Finance, HR, IT, Sales). None of them received an admin role (least privilege).

![Users list](screenshots/lab2-03-users-list.png)

Created one security group per department so access is granted by role, not by individual.

![Department groups](screenshots/lab2-04-groups.png)

### 3. P2 licensing

Activated the Entra ID P2 trial and assigned licenses to the 8 employees and the admin (9 assigned).

![P2 licenses](screenshots/lab2-05-p2-license.png)

### 4. Dynamic group

Created `DYN-Finance` with the rule `user.department -eq "Finance"`. Entra added Maya Chen and Jordan Ellis automatically, and rule processing reported **Succeeded**. No one added them by hand.

![Dynamic group overview](screenshots/lab2-06-dynamic-group-overview.png)
![Dynamic group members](screenshots/lab2-07-dynamic-members.png)

### 5. Conditional Access

Turned off security defaults (Microsoft's one-size-fits-all baseline) so custom policies could replace them.

![Security defaults disabled](screenshots/lab2-08-security-defaults-off.png)

Built 3 policies, all starting in **report-only** mode:

| Policy | Who | Control |
| --- | --- | --- |
| CA01 – Require MFA – All users | All users (break-glass excluded) | Require MFA |
| CA02 – Block legacy authentication | All users (break-glass excluded) | Block Exchange ActiveSync and other legacy clients |
| CA03 – Admins – MFA and daily sign-in | Global Administrator, User Administrator roles | Require MFA + sign-in frequency of 1 day |

![CA01 settings](screenshots/lab2-09-ca01-settings.png)
![Policy list](screenshots/lab2-10-ca-policy-list.png)
![CA03 details](screenshots/lab2-10b-ca03-details.png)

### 6. PIM: just-in-time admin access

Made Lena Novak (Systems Administrator) **eligible** for User Administrator instead of giving her the role permanently.

![PIM eligible assignment](screenshots/lab2-14-pim-eligible.png)

Role settings: activation lasts at most 2 hours, requires MFA, requires a written justification, and requires approval from Beka Admin.

![PIM role settings](screenshots/lab2-15-pim-settings.png)

### 7. Access review: catching access that nobody cleaned up

**Scenario:** Jordan Ellis transferred from Finance to Sales (HR ticket #1002), but his membership in `SG-Finance` was never removed. This is *access creep*, one of the most common audit findings. A quarterly access review is the control that catches it.

Created **Q4 2026 – SG-Finance membership review** in Identity Governance:

| Setting | Value | Why |
| --- | --- | --- |
| Scope | All members of `SG-Finance` | Finance access is sensitive |
| Reviewer | Beka Admin (selected reviewer) | A named person is accountable |
| Recurrence | Quarterly, no end date | Matches a typical audit cycle |
| Auto-apply results | Enabled | Denied users are removed without a manual step |
| If reviewers don't respond | Remove access | Access has to be re-justified, not kept by default |
| Decision helpers | Enabled (no sign-in for 30 days) | Flags inactive accounts for the reviewer |
| Justification required | Enabled | Every decision has a written reason for auditors |

![Access review settings](screenshots/lab2-19-access-review-settings.png)

As the reviewer, Entra's decision helper already recommended **Deny** for Jordan, flagged as an *Inactive user*, and **Approve** for Maya Chen.

![Reviewer view with recommendations](screenshots/lab2-20-access-review-recommendations.png)

I recorded both decisions with a written reason:

- **Maya Chen: Approved.** *"Accountant in Finance – access confirmed."*
- **Jordan Ellis: Denied.** *"Transferred to Sales per HR ticket #1002 – Finance access no longer required."*

![Approve and deny with justification](screenshots/lab2-21-access-review-decisions.png)
![Decisions recorded](screenshots/lab2-22-access-review-recorded.png)

I stopped the review and applied the results. The overview shows the final tally: 2 users reviewed, 1 approved, 1 denied, 0 not reviewed.

![Review results](screenshots/lab2-23-access-review-results.png)

Because auto-apply was enabled, Entra **removed Jordan from `SG-Finance` automatically**. Maya is now the only member.

![SG-Finance after the review](screenshots/lab2-24-sg-finance-after-review.png)

> **Why this mattered later:** `SG-Finance` is one of the groups I federate to AWS in [Lab 4](../04-aws/README.md). Because the review removed Jordan first, he was never provisioned into AWS at all. Cleaning up identity at the source keeps stale access from spreading to every connected system.

---

## Validation

**Conditional Access, report-only.** Signed in as Maya Chen (a standard Finance user) and checked her sign-in in the Sign-in logs:

- CA01: *Report-only: User action required*, meaning it would have required MFA
- CA02: *Not applied*, because she used a modern browser
- CA03: *Not applied*, because she is not an admin

![Report-only result](screenshots/lab2-11-report-only-result.png)

**What If tool.** Simulating Maya signing in to Office 365 showed CA01 applies, while CA02 and CA03 do not, each with its reason.

![What If – will apply](screenshots/lab2-12-what-if-will-apply.png)
![What If – will not apply](screenshots/lab2-12b-what-if-will-not-apply.png)

**PIM, end to end.** Signed in as Lena and requested activation with the reason *"Ticket #1001: reset password for new hire."*

![Activation request](screenshots/lab2-16-pim-request.png)
![Pending approval](screenshots/lab2-16b-pim-pending.png)

As Beka Admin, I approved it with a documented justification. The approval panel shows the role ending exactly 2 hours after it started.

![Approval](screenshots/lab2-17-pim-approve.png)

The PIM resource audit captured the full chain: eligible assignment, role-setting change, Lena's request, my approval, and the completed activation. Every step is timestamped and tied to a named person.

![PIM audit log](screenshots/lab2-18-pim-audit.png)

---

## Security decisions

- **Break-glass account** is excluded from all Conditional Access policies and has a long, separately stored password.
- **Report-only first.** Every policy was tested against real sign-ins and the What If tool before anyone could be blocked.
- **Admin coverage.** When creating CA01, Entra warned about locking myself out, so I excluded my admin account from CA01. Admins are covered by the stricter CA03 instead, which requires MFA and daily re-authentication.
- **No standing admin rights for staff.** Lena's admin access is eligible only, time-boxed to 2 hours, and needs approval.
- **Separate MFA registration per test user**, to mirror real per-user enrollment.
- **Access reviews remove by default.** If a reviewer doesn't respond, access is removed, and denied users are removed automatically, so keeping access always requires a decision.

## What went wrong and how I fixed it

- **Locked out after a break.** When I came back to the lab three weeks later, I couldn't sign in as my admin. I used the recovery path I'd set up for exactly this situation, which proved why a break-glass account matters.
- **Test sign-in wasn't showing in the logs.** Sign-in logs only showed my admin's attempts at first. Private browser windows in the same browser share one session, so I used separate browsers for the admin and the test user, filtered the logs by user, and allowed time for the logs to catch up.
- **Misreading a policy summary.** CA03's summary said "Client apps: 1 included," which looked like the policy only covered one app type. Opening the policy showed Client apps as *Not configured*, which means **all** clients. I verified the setting itself instead of trusting the summary.
- **What If needed a specific app.** The What If tool wouldn't run on "all apps," so I simulated Office 365, the bundle employees actually use.
- **Denied user still in the group.** After I finished my decisions, My Access showed the review as completed, but Jordan was still in `SG-Finance`. Decisions aren't enforced until the review **ends**. I found **Stop** under the review's current instance, stopped it, then applied the results. Jordan was removed automatically.

## What I'd do in production

- Roll out MFA to a pilot group first, and tell users before enforcement starts.
- Switch CA01 and CA02 from report-only to **On** after a monitoring period.
- Alert on any break-glass sign-in, and test it on a schedule.
- Remove Global Administrator from the original owner account once the dedicated admin and break-glass accounts are proven.
- Extend **access reviews** beyond `SG-Finance` to privileged roles (through PIM), every group that grants app access, and guest users. Assign group owners or managers as reviewers instead of one admin.
- Use group-based licensing so new hires get licenses automatically.

## Skills demonstrated

Microsoft Entra ID · Conditional Access · Multi-factor authentication · Privileged Identity Management (PIM) · Access reviews (identity governance) · RBAC · Dynamic groups · Least privilege · Zero Trust · Sign-in log analysis · Audit evidence
