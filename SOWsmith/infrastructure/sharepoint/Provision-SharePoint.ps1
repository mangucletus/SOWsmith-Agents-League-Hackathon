<#
.SYNOPSIS
  Provision the SharePoint Online site for the Bid Package Generator (SOW/RFP) POC: document
  libraries, the Reviewers + AuditLog lists, and upload the knowledge base.

.DESCRIPTION
  Uses the PnP.PowerShell module. Idempotent — safe to re-run (skips items that exist).
  Creates: Approved-Exemplars, Reference-Library, Templates, Drafts, Approved, Rejected
  document libraries; Reviewers and AuditLog lists; then uploads the local KB files.

.PREREQUISITES
  Install-Module PnP.PowerShell -Scope CurrentUser
  (and an account with permission to create lists/libraries on the target site)

.EXAMPLE
  ./Provision-SharePoint.ps1 -SiteUrl "https://contoso.sharepoint.com/sites/POC-BidPackage"

.NOTES
  Reviewer emails are seeded as TEXT (robust for a POC even if those users don't yet exist
  in the tenant). Switch ReviewerEmail/LegalReviewerEmail to People columns later if desired.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)] [string] $SiteUrl,
  [string] $KbPath
)

$ErrorActionPreference = "Stop"
if (-not $KbPath) {
  $repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
  $KbPath = Join-Path $repo "knowledge-base/sharepoint-online-knowledge-base"
}
if (-not (Test-Path $KbPath)) { throw "Knowledge base folder not found: $KbPath" }

Write-Host "Connecting to $SiteUrl ..." -ForegroundColor Cyan
Connect-PnPOnline -Url $SiteUrl -Interactive

function Ensure-Library($title) {
  if (-not (Get-PnPList -Identity $title -ErrorAction SilentlyContinue)) {
    New-PnPList -Title $title -Template DocumentLibrary -OnQuickLaunch | Out-Null
    Write-Host "  + library '$title'" -ForegroundColor Green
  } else { Write-Host "  = library '$title' exists" }
}

function Ensure-Field($list, $internal, $display, $type, [string[]]$choices) {
  $existing = Get-PnPField -List $list -Identity $internal -ErrorAction SilentlyContinue
  if ($existing) { return }
  if ($type -eq "Choice") {
    Add-PnPField -List $list -DisplayName $display -InternalName $internal -Type Choice -Choices $choices -AddToDefaultView | Out-Null
  } else {
    Add-PnPField -List $list -DisplayName $display -InternalName $internal -Type $type -AddToDefaultView | Out-Null
  }
  Write-Host "    + field '$display' ($type) on '$list'" -ForegroundColor Green
}

# 1) Document libraries -------------------------------------------------------
"Approved-Exemplars","Reference-Library","Templates","Drafts","Approved","Rejected" |
  ForEach-Object { Ensure-Library $_ }

# 2) Reviewers list -----------------------------------------------------------
if (-not (Get-PnPList -Identity "Reviewers" -ErrorAction SilentlyContinue)) {
  New-PnPList -Title "Reviewers" -Template GenericList -OnQuickLaunch | Out-Null
  Write-Host "  + list 'Reviewers'" -ForegroundColor Green
}
$serviceTypes = @("Pipeline Construction","Facility Maintenance","Electrical & Instrumentation",
  "Civil & Earthwork","Coating & Insulation","Hydrotesting & Commissioning","Fabrication",
  "Cathodic Protection","Pipeline Integrity","Demolition & Abandonment","Station & Terminal",
  "Welding Services")
Ensure-Field "Reviewers" "ServiceType" "ServiceType" "Choice" $serviceTypes
Ensure-Field "Reviewers" "ReviewerEmail" "ReviewerEmail" "Text"
Ensure-Field "Reviewers" "LegalReviewerEmail" "LegalReviewerEmail" "Text"

# Seed reviewer routing (ServiceType, Supply Chain ReviewerEmail, Legal/Contracts LegalReviewerEmail)
$reviewers = @(
  @("Pipeline Construction","mark.davis@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Facility Maintenance","jen.alvarez@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Electrical & Instrumentation","tom.nguyen@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Civil & Earthwork","mark.davis@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Coating & Insulation","jen.alvarez@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Hydrotesting & Commissioning","tom.nguyen@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Fabrication","mark.davis@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Cathodic Protection","tom.nguyen@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Pipeline Integrity","jen.alvarez@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Demolition & Abandonment","mark.davis@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Station & Terminal","jen.alvarez@sowsmithusa.com","robert.hayes@sowsmithusa.com"),
  @("Welding Services","tom.nguyen@sowsmithusa.com","robert.hayes@sowsmithusa.com")
)
$existingTypes = (Get-PnPListItem -List "Reviewers" -PageSize 500).FieldValues.ServiceType
foreach ($r in $reviewers) {
  if ($existingTypes -contains $r[0]) { continue }
  Add-PnPListItem -List "Reviewers" -Values @{ Title = $r[0]; ServiceType = $r[0]
    ReviewerEmail = $r[1]; LegalReviewerEmail = $r[2] } | Out-Null
}
Write-Host "  = seeded $($reviewers.Count) reviewer routes" -ForegroundColor Green

# 3) AuditLog list ------------------------------------------------------------
if (-not (Get-PnPList -Identity "AuditLog" -ErrorAction SilentlyContinue)) {
  New-PnPList -Title "AuditLog" -Template GenericList -OnQuickLaunch | Out-Null
  Write-Host "  + list 'AuditLog'" -ForegroundColor Green
}
Ensure-Field "AuditLog" "DraftFileName" "DraftFileName" "Text"
Ensure-Field "AuditLog" "Author" "Author" "Text"
Ensure-Field "AuditLog" "Reviewer" "Reviewer" "Text"
Ensure-Field "AuditLog" "Action" "Action" "Text"
Ensure-Field "AuditLog" "ReviewStatus" "ReviewStatus" "Text"
Ensure-Field "AuditLog" "Comments" "Comments" "Note"

# 4) Upload the knowledge base ------------------------------------------------
function Upload-Folder($localSub, $library) {
  $dir = Join-Path $KbPath $localSub
  if (-not (Test-Path $dir)) { return }
  Get-ChildItem -Path $dir -File | Where-Object { $_.Name -notlike "_*" } | ForEach-Object {
    Add-PnPFile -Path $_.FullName -Folder $library | Out-Null
    Write-Host "    ^ $library/$($_.Name)"
  }
}
Write-Host "Uploading knowledge base..." -ForegroundColor Cyan
Upload-Folder "Approved-Exemplars" "Approved-Exemplars"
Upload-Folder "Reference-Library"  "Reference-Library"
Upload-Folder "Templates"          "Templates"

Write-Host "`nDone. Next: scope Copilot Studio Topic 1 -> Approved-Exemplars, Topic 2 -> Reference-Library." -ForegroundColor Cyan
Write-Host "See ../../copilot-studio/knowledge-scoping.md and ../../approval-workflow/flow-definition.md."
