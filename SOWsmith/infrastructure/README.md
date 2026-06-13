# `infrastructure/` — stand up the real SharePoint

Scripts that build the **actual** SharePoint Online site for the POC (the **Knowledge Base** +
output libraries + governance lists in the architecture diagram) and upload the knowledge base.

> You still create the **site** itself in SharePoint (or via your tenant's site-provisioning
> process) — pick a **default-themed** team/communication site named `POC-BidPackage`. These
> scripts then create everything inside it. They cannot run from this sandbox (they need your
> authenticated tenant); run them from your machine.

## Option A — PnP PowerShell (recommended on Windows)
```powershell
Install-Module PnP.PowerShell -Scope CurrentUser
./sharepoint/Provision-SharePoint.ps1 -SiteUrl "https://<tenant>.sharepoint.com/sites/POC-BidPackage"
```

## Option B — CLI for Microsoft 365 (cross-platform)
```bash
npm i -g @pnp/cli-microsoft365
m365 login
./sharepoint/provision-m365cli.sh "https://<tenant>.sharepoint.com/sites/POC-BidPackage"
```

## What the scripts create
- **Document libraries:** `Approved-Exemplars`, `Reference-Library`, `Templates`, `Drafts`, `Approved`, `Rejected`
- **Lists:** `Reviewers` (ServiceType, ReviewerEmail, LegalReviewerEmail) seeded with the 12 service-type routes;
  `AuditLog` (DraftFileName, Author, Reviewer, Action, ReviewStatus, Comments) left empty
- **Upload:** the contents of `knowledge-base/sharepoint-online-knowledge-base/` into the matching libraries

See [`sharepoint/columns.md`](sharepoint/columns.md) for the exact list schemas, and
[`../docs/MANUAL-SETUP.md`](../docs/MANUAL-SETUP.md) for the full end-to-end setup order.

**Note on reviewer emails:** seeded as **Text** so they work even before those users exist in your
tenant. Replace with your real reviewers' addresses, or convert the columns to **Person** type once
the accounts exist.
