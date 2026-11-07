-- Edao Logistics - identity governance findings
-- Each query starts with "-- name: <ID> <title>". 07_run_findings.py runs them in order.
-- Users are matched to HR by display name (a lab simplification; production would use employeeId).

-- name: F01 Terminated in HR but account still enabled
SELECT h.display_name,
       h.department,
       h.effective_date AS terminated_on,
       CAST(julianday('now') - julianday(h.effective_date) AS INTEGER) AS days_since_termination,
       'High' AS risk
FROM hr h
JOIN users u ON u.display_name = h.display_name
WHERE h.status = 'Terminated'
  AND u.account_enabled = 'True';

-- name: F02 Mover not processed (HR and Entra departments differ)
SELECT h.display_name,
       h.department AS hr_department,
       u.department AS entra_department,
       h.effective_date AS changed_on,
       (SELECT group_concat(g.group_name, ', ')
          FROM group_memberships g
         WHERE g.user_id = u.user_id) AS current_groups,
       'High' AS risk
FROM hr h
JOIN users u ON u.display_name = h.display_name
WHERE h.status = 'Active'
  AND COALESCE(u.department, '') <> h.department;

-- name: F03 Separation-of-duties conflict
SELECT s.rule_id,
       a.display_name,
       a.group_name AS group_a,
       b.group_name AS group_b,
       s.risk,
       s.reason
FROM sod_rules s
JOIN group_memberships a ON a.group_name LIKE s.group_a
JOIN group_memberships b ON b.user_id = a.user_id
                        AND b.group_name LIKE s.group_b
                        AND b.group_name <> a.group_name
JOIN users u ON u.user_id = a.user_id AND u.account_enabled = 'True'
ORDER BY s.rule_id, a.display_name;

-- name: F04 Admin role without MFA
SELECT u.display_name,
       group_concat(DISTINCT r.role) AS roles,
       group_concat(DISTINCT r.assignment) AS assignment_type,
       COALESCE(m.mfa_registered, 'Unknown') AS mfa_registered,
       'High' AS risk
FROM role_assignments r
JOIN users u ON u.user_id = r.user_id
LEFT JOIN mfa m ON m.user_id = u.user_id
WHERE u.account_enabled = 'True'
  AND COALESCE(m.mfa_registered, 'False') <> 'True'
GROUP BY u.user_id, u.display_name, m.mfa_registered;

-- name: F05 Account with no HR record (needs a named owner)
SELECT u.display_name,
       u.user_type,
       CASE WHEN EXISTS (SELECT 1 FROM role_assignments r WHERE r.user_id = u.user_id)
            THEN 'Yes' ELSE 'No' END AS has_admin_role,
       'Medium' AS risk
FROM users u
LEFT JOIN hr h ON h.display_name = u.display_name
WHERE h.employee_id IS NULL
  AND u.account_enabled = 'True';

-- name: F06 Enabled account never used or inactive 30+ days
SELECT u.display_name,
       u.department,
       u.created,
       COALESCE(NULLIF(u.last_sign_in, ''), 'never') AS last_sign_in,
       CAST(julianday('now') - julianday(COALESCE(NULLIF(u.last_sign_in, ''), u.created)) AS INTEGER) AS days_inactive,
       'Medium' AS risk
FROM users u
WHERE u.account_enabled = 'True'
  AND (u.last_sign_in = '' OR julianday('now') - julianday(u.last_sign_in) >= 30);

-- name: F07 Enabled user without MFA
SELECT u.display_name,
       u.department,
       'Medium' AS risk
FROM users u
JOIN mfa m ON m.user_id = u.user_id
WHERE u.account_enabled = 'True'
  AND m.mfa_registered <> 'True'
  AND m.is_admin <> 'True';

-- name: F08 Employee missing first or last name (blocks SCIM provisioning)
SELECT u.display_name,
       u.department,
       'Low' AS risk
FROM users u
JOIN hr h ON h.display_name = u.display_name
WHERE u.account_enabled = 'True'
  AND (u.given_name = '' OR u.surname = '');