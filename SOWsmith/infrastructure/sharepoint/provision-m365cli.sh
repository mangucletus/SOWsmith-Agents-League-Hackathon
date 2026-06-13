#!/usr/bin/env bash
# Provision the Bid Package Generator (SOW/RFP) SharePoint site with the CLI for Microsoft 365 (m365).
# Alternative to Provision-SharePoint.ps1 for teams who prefer the cross-platform CLI.
#
# Prerequisites:
#   npm i -g @pnp/cli-microsoft365
#   m365 login
# Usage:
#   ./provision-m365cli.sh "https://contoso.sharepoint.com/sites/POC-BidPackage"
set -euo pipefail

SITE_URL="${1:?Usage: ./provision-m365cli.sh <site-url>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
KB="$(cd "$HERE/../.." && pwd)/knowledge-base/sharepoint-online-knowledge-base"
[ -d "$KB" ] || { echo "KB not found: $KB" >&2; exit 1; }

echo "Creating document libraries..."
for lib in "Approved-Exemplars" "Reference-Library" "Templates" "Drafts" "Approved" "Rejected"; do
  m365 spo list add --webUrl "$SITE_URL" --title "$lib" --baseTemplate DocumentLibrary 2>/dev/null \
    && echo "  + $lib" || echo "  = $lib (exists)"
done

echo "Creating Reviewers list + columns..."
m365 spo list add --webUrl "$SITE_URL" --title "Reviewers" --baseTemplate GenericList 2>/dev/null || true
m365 spo field add --webUrl "$SITE_URL" --listTitle "Reviewers" \
  --xml '<Field Type="Choice" DisplayName="ServiceType" Name="ServiceType"><CHOICES><CHOICE>Pipeline Construction</CHOICE><CHOICE>Facility Maintenance</CHOICE><CHOICE>Electrical &amp; Instrumentation</CHOICE><CHOICE>Civil &amp; Earthwork</CHOICE><CHOICE>Coating &amp; Insulation</CHOICE><CHOICE>Hydrotesting &amp; Commissioning</CHOICE><CHOICE>Fabrication</CHOICE><CHOICE>Cathodic Protection</CHOICE><CHOICE>Pipeline Integrity</CHOICE><CHOICE>Demolition &amp; Abandonment</CHOICE><CHOICE>Station &amp; Terminal</CHOICE><CHOICE>Welding Services</CHOICE></CHOICES></Field>' 2>/dev/null || true
m365 spo field add --webUrl "$SITE_URL" --listTitle "Reviewers" --xml '<Field Type="Text" DisplayName="ReviewerEmail" Name="ReviewerEmail"/>' 2>/dev/null || true
m365 spo field add --webUrl "$SITE_URL" --listTitle "Reviewers" --xml '<Field Type="Text" DisplayName="LegalReviewerEmail" Name="LegalReviewerEmail"/>' 2>/dev/null || true

echo "Seeding reviewer routes..."
# ServiceType|ReviewerEmail (Supply Chain)|LegalReviewerEmail (Legal/Contracts)
ROWS=(
"Pipeline Construction|mark.davis@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Facility Maintenance|jen.alvarez@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Electrical & Instrumentation|tom.nguyen@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Civil & Earthwork|mark.davis@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Coating & Insulation|jen.alvarez@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Hydrotesting & Commissioning|tom.nguyen@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Fabrication|mark.davis@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Cathodic Protection|tom.nguyen@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Pipeline Integrity|jen.alvarez@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Demolition & Abandonment|mark.davis@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Station & Terminal|jen.alvarez@sowsmithusa.com|robert.hayes@sowsmithusa.com"
"Welding Services|tom.nguyen@sowsmithusa.com|robert.hayes@sowsmithusa.com"
)
for row in "${ROWS[@]}"; do IFS='|' read -r pt rev leg <<< "$row"
  m365 spo listitem add --webUrl "$SITE_URL" --listTitle "Reviewers" \
    --Title "$pt" --ServiceType "$pt" --ReviewerEmail "$rev" --LegalReviewerEmail "$leg" >/dev/null 2>&1 || true
done

echo "Creating AuditLog list + columns..."
m365 spo list add --webUrl "$SITE_URL" --title "AuditLog" --baseTemplate GenericList 2>/dev/null || true
for col in DraftFileName Author Reviewer Action ReviewStatus; do
  m365 spo field add --webUrl "$SITE_URL" --listTitle "AuditLog" --xml "<Field Type=\"Text\" DisplayName=\"$col\" Name=\"$col\"/>" 2>/dev/null || true
done
m365 spo field add --webUrl "$SITE_URL" --listTitle "AuditLog" --xml '<Field Type="Note" DisplayName="Comments" Name="Comments"/>' 2>/dev/null || true

echo "Uploading knowledge base..."
upload() { local sub="$1" lib="$2"
  for f in "$KB/$sub"/*; do
    [ -f "$f" ] || continue; case "$(basename "$f")" in _*) continue;; esac
    m365 spo file add --webUrl "$SITE_URL" --folder "$lib" --path "$f" >/dev/null && echo "  ^ $lib/$(basename "$f")"
  done
}
upload "Approved-Exemplars" "Approved-Exemplars"
upload "Reference-Library"  "Reference-Library"
upload "Templates"          "Templates"

echo "Done. Now scope Copilot Studio topics (see ../../copilot-studio/knowledge-scoping.md)."
