# Edao Logistics - build the Active Directory structure (run once)
Import-Module ActiveDirectory
$domainDN = (Get-ADDomain).DistinguishedName
$root     = "OU=Edao,$domainDN"

New-ADOrganizationalUnit -Name "Edao" -Path $domainDN
foreach ($ou in "Users", "Groups", "Disabled Users", "Service Accounts") {
    New-ADOrganizationalUnit -Name $ou -Path $root
    Write-Host "[+] OU $ou"
}

foreach ($dept in "Finance", "HR", "IT", "Operations", "Sales") {
    New-ADOrganizationalUnit -Name $dept -Path "OU=Users,$root"
    New-ADGroup -Name "AD-$dept" -GroupScope Global -GroupCategory Security `
                -Path "OU=Groups,$root" -Description "All $dept staff"
    Write-Host "[+] OU Users\$dept and group AD-$dept"
}

Write-Host "`nStructure complete."
