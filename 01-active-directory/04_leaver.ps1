# Edao Logistics - LEAVER: offboard a departing employee
param(
    [Parameter(Mandatory)] [string]$User,
    [Parameter(Mandatory)] [string]$Ticket
)
Import-Module ActiveDirectory

$domainDN   = (Get-ADDomain).DistinguishedName
$disabledOU = "OU=Disabled Users,OU=Edao,$domainDN"
$log        = "C:\Lab\lifecycle_log.csv"
$today      = Get-Date -Format "yyyy-MM-dd"

$u = Get-ADUser -Identity $User -Properties Department, Title, MemberOf
$groups = $u.MemberOf | ForEach-Object { (Get-ADGroup $_).Name }

Write-Host "`nLEAVER: $($u.Name) ($($u.Department), $($u.Title))"
Write-Host "  Groups: $($groups -join ', ')"
Write-Host "  Ticket: $Ticket"
# -cne = case-sensitive: only an exact, uppercase YES continues
if ((Read-Host "Type YES to offboard this user") -cne "YES") { Write-Host "Cancelled. Nothing changed."; return }

function Write-Log($action, $detail) {
    Write-Host "[+] $action - $detail"
    [pscustomobject]@{ time = Get-Date -Format s; action = "LEAVER - $action"
                       user = $u.SamAccountName; detail = $detail } |
        Export-Csv $log -Append -NoTypeInformation
}

# 1. Disable the account (stops new sign-ins)
Disable-ADAccount -Identity $u
Write-Log "Account disabled" "Enabled = False"

# 2. Scramble the password (no one knows it, old password can't be reused)
$random = -join ((48..57) + (65..90) + (97..122) + (33..47) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
Set-ADAccountPassword -Identity $u -Reset -NewPassword (ConvertTo-SecureString $random -AsPlainText -Force)
Write-Log "Password reset" "random 32-character value, not stored"

# 3. Remove every group membership
foreach ($g in $groups) {
    Remove-ADGroupMember -Identity $g -Members $u -Confirm:$false
    Write-Log "Removed from group" $g
}

# 4. Stamp the reason for auditors
Set-ADUser -Identity $u -Description "Disabled $today - $Ticket - former $($u.Department) $($u.Title)"
Write-Log "Description stamped" "Disabled $today - $Ticket"

# 5. Move to Disabled Users OU
Move-ADObject -Identity $u.DistinguishedName -TargetPath $disabledOU
Write-Log "Moved" "OU=Disabled Users"

Write-Host "`nOffboarding complete. Logged to $log"
