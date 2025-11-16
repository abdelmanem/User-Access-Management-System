<# 
    Export Active Directory users into a CSV that matches the
    Access Management System import format.

    Prerequisites:
      - Run on a domain-joined machine with RSAT / ActiveDirectory module.
      - Execute in a PowerShell session with sufficient AD privileges.

    The script writes C:\ADUsers.csv. Adjust $ExportPath as needed.
#>

Import-Module ActiveDirectory -ErrorAction Stop

$ExportPath = "C:\ADUsers.csv"

Get-ADUser -Filter * -Properties `
    mail,
    givenName,
    sn,
    employeeID,
    telephoneNumber,
    mobile,
    title,
    department,
    enabled,
    whenCreated,
    description,
    office,
    streetAddress,
    l,
    st,
    postalCode,
    co |
Select-Object `
    @{Name = 'username'; Expression = { $_.SamAccountName }},
    @{Name = 'email'; Expression = { $_.mail }},
    @{Name = 'first_name'; Expression = { $_.givenName }},
    @{Name = 'last_name'; Expression = { $_.sn }},
    @{Name = 'employee_id'; Expression = { $_.employeeID }},
    @{Name = 'phone_primary'; Expression = { $_.telephoneNumber }},
    @{Name = 'phone_secondary'; Expression = { $_.mobile }},
    @{Name = 'position'; Expression = { $_.title }},
    @{Name = 'employment_type'; Expression = { 'Full-time' }},
    @{Name = 'employment_status'; Expression = { if ($_.Enabled) { 'Active' } else { 'Inactive' } }},
    @{Name = 'department_name'; Expression = { $_.department }},
    @{Name = 'is_active'; Expression = { $_.Enabled }},
    @{Name = 'join_date'; Expression = { $_.whenCreated.ToString('yyyy-MM-dd') }},
    @{Name = 'description'; Expression = { $_.description }},
    @{Name = 'office_location'; Expression = { $_.office }},
    @{Name = 'work_address'; Expression = { $_.streetAddress }},
    @{Name = 'city'; Expression = { $_.l }},
    @{Name = 'state_province'; Expression = { $_.st }},
    @{Name = 'postal_code'; Expression = { $_.postalCode }},
    @{Name = 'country'; Expression = { $_.co }} |
Export-Csv -Path $ExportPath -NoTypeInformation -Encoding UTF8

Write-Host "Export completed. File saved at $ExportPath"

