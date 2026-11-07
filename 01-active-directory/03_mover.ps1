# Edao Logistics - MOVER: transfer an employee to a new department
param(
    [Parameter(Mandatory)] [string]$User,
    [Parameter(Mandatory)] [string]$NewDepartment,
    [Parameter(Mandatory)] [string]$NewTitle
)
Import-Module ActiveDirectory

$domainDN = (Get-ADDomain).DistinguishedName
$newOU    = "OU=$NewDepartment,OU=Users,OU=Edao,$domainDN"
$log      = "C:\Lab\lifecycle_log.csv"

$u = Get-ADUser -Identity $User -Properties Department, Title, MemberOf
$oldDept = $u.Department
$oldGroups = $u.MemberOf | ForEach-Object { (Get-ADGroup $_).Name }

Write-Host "`nMOVER: $($u.Name)"
Write-Host "  From: $oldDept / $($u.Title)   Groups: $($oldGroups -join ', ')"
Write-Host "  To:   $NewDepartment / $NewTitle"
# -cne = case-sensitive: only an exact, uppercase YES continues
if ((Read-Host "Type YES to continue") -cne "YES") { Write-Host "Cancelled. Nothing changed."; return }

# 1. Remove old department access first (least privilege)
foreach ($g in $oldGroups | Where-Object { $_ -like "AD-*" }) {
    Remove-ADGroupMember -Identity $g -Members $u -Confirm:$false
    Write-Host "[-] Removed from $g"
}
# 2. Update HR attributes
Set-ADUser -Identity $u -Department $NewDepartment -Title $NewTitle
Write-Host "[+] Department = $NewDepartment, Title = $NewTitle"
# 3. Move to the new department OU
Move-ADObject -Identity $u.DistinguishedName -TargetPath $newOU
Write-Host "[+] Moved to OU $NewDepartment"
# 4. Grant new department access
Add-ADGroupMember -Identity "AD-$NewDepartment" -Members $u
Write-Host "[+] Added to AD-$NewDepartment"

[pscustomobject]@{
    time   = Get-Date -Format s
    action = "MOVER"
    user   = $u.SamAccountName
    detail = "$oldDept -> $NewDepartment; title=$NewTitle; removed=$($oldGroups -join '|'); added=AD-$NewDepartment"
} | Export-Csv $log -Append -NoTypeInformation
Write-Host "`nMover complete. Logged to $log"
