# Edao Logistics - JOINER: create new hires from an HR CSV
param([string]$CsvPath = "C:\Lab\new_hires.csv")
Import-Module ActiveDirectory

$domain   = Get-ADDomain
$usersOU  = "OU=Users,OU=Edao,$($domain.DistinguishedName)"
$log      = "C:\Lab\lifecycle_log.csv"

# One temporary password for this batch; never saved, must be changed at first sign-in
$tempPw = Read-Host "Temporary password for new hires" -AsSecureString

foreach ($h in Import-Csv $CsvPath) {
    $sam  = ("{0}.{1}" -f $h.FirstName, $h.LastName).ToLower()
    $name = "$($h.FirstName) $($h.LastName)"

    if (Get-ADUser -Filter "SamAccountName -eq '$sam'") {
        Write-Host "[skip] $sam already exists"
        continue
    }

    New-ADUser -Name $name -DisplayName $name `
        -GivenName $h.FirstName -Surname $h.LastName `
        -SamAccountName $sam -UserPrincipalName "$sam@$($domain.DNSRoot)" `
        -EmployeeID $h.EmployeeID -Department $h.Department -Title $h.Title `
        -Path "OU=$($h.Department),$usersOU" `
        -AccountPassword $tempPw -ChangePasswordAtLogon $true -Enabled $true

    Add-ADGroupMember -Identity "AD-$($h.Department)" -Members $sam
    Write-Host "[+] $name created in $($h.Department) and added to AD-$($h.Department)"

    [pscustomobject]@{
        time   = Get-Date -Format s
        action = "JOINER"
        user   = $sam
        detail = "OU=$($h.Department); group=AD-$($h.Department); title=$($h.Title)"
    } | Export-Csv $log -Append -NoTypeInformation
}
Write-Host "`nJoiner complete. Actions logged to $log"
