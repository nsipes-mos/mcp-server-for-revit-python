# Autodesk Marketplace publication

Target: this repository's complete local MCP server, published through Autodesk's
Design and Make Marketplace. A prepared manifest is not a submitted or approved
listing. This candidate preserves all 20 tools. Autodesk's own product-help catalog
is not a self-service registry for community servers.

## Candidate artifacts

- `mcp-tool-manifest.json`: generated from the actual registered FastMCP inventory.
- `PRIVACY.md`: model data, AI-client disclosure, storage, retention and revocation.
- `SECURITY.md`: pairing, request review, loopback and code-execution boundaries.
- `docs/publisher-declaration-draft.md`: evidence and unresolved form attestations.
- `docs/marketplace-listing-draft.md`: listing text and installation/reviewer steps.

Regenerate with `uv run python scripts/export_mcp_manifest.py`; verify with
`uv run python scripts/export_mcp_manifest.py --check`. The pinned SDK supplies
the declared protocol version. Runtime descriptions share a catalog with the
manifest; implementation docstrings remain developer documentation.

## Required work before submission

1. Maintainer validates and merges the publication PR. Freeze the exact commit
   and lockfile used in the submitted package; do not submit an unmerged candidate
   as a production release. New tools, code or connections require a new inventory
   and Autodesk review.
2. Obtain Autodesk's written decision about the unrestricted Python execution tool,
   whose user-supplied code can contact arbitrary destinations or read unrelated
   data. `external_endpoints: []` describes the built-in client only and is **not**
   a claim that supplied code cannot initiate external communication. Do not attest
   that every possible endpoint/data category is bounded. Confirm the local HTTP
   loopback bridge is acceptable under the Local (A) model's HTTPS requirement.
3. Confirm pyRevit-dependent packaging with Autodesk. The existing install requires
   pyRevit, Routes configuration and MCP-client pairing. Ribbon commands do not
   establish compliance with the ready-after-install rule or replace the required
   add-in/bundle installer. Autodesk offers custom packaging; agree a package that
   installs dependencies and initializes Routes without manual file copying.
4. Validate a clean install, consent, all 20 tools and uninstall on Revit 2027/Windows
   with the supported pyRevit version. Record exact versions and test results. Test
   any other Revit years before declaring them compatible. Existing open stability/
   document-lifecycle work must be reconciled with the final candidate.
5. Run a dependency/security scan and resolve high-severity findings before signing.
   Unit tests and an SDK upgrade do not constitute a clean vulnerability scan.
6. Confirm third-party licensing for the GPL-3.0 pyRevit dependency and include the
   required Marketplace end-user agreement. This repository's MIT license alone
   does not establish eligibility of the final dependency/package arrangement.
7. Complete the publisher profile, public privacy-policy URL and assets. An
   authorized publisher must review and accept any Publisher Agreement at the
   point Autodesk presents it, and sign only truthful declaration attestations.
8. Complete the MCP Publisher Declaration Form with the exact package's manifest,
   then submit the listing/package in Publisher Corner. Retain confirmation IDs.
   Answer reviewer feedback, review Autodesk's prepared installer and verify the
   final public Marketplace listing before calling publication complete.

## Publisher Corner submission checklist

The live App Submission Guidelines dialog checked on 14 October 2026 adds these
mandatory prerequisites. A saved draft does not prove they have been met:

- Detailed app description and general usage instructions of at least 1,500
  characters each. The listing draft includes text above both thresholds.
- A clear graphical app icon, at least four workflow screenshots, and a workflow
  video if available. Capture the exact candidate in Revit; do not present unit
  tests or another product's UI as runtime screenshots.
- Binary app files and complete installation/uninstallation instructions. The
  source review ZIP does not replace the required installable package; confirm
  how Autodesk handles Python/pyRevit packaging before submission.
- Compatibility with the latest Autodesk product version, graceful input/error
  handling, no fatal errors, and verified uninstall behavior.
- F1 help on the ribbon. The Connect, Disconnect and Privacy command bundles use
  pyRevit's documented `help_url` metadata to open their relevant public help.
  Verify the actual ribbon F1 behavior in the clean Revit 2027 validation.
- Company URL, public publisher privacy-policy URL and a three-part version number.

The default Marketplace end-user agreement restricts redistribution and
modification. Obtain an MIT-preserving end-user agreement that also meets the
Publisher Agreement's required terms; do not silently replace the repository's
MIT license with the default proprietary restrictions.

## Current requirements verified 14 October 2026

- [MCP publisher guide](https://aps.autodesk.com/marketplace/mcp-publisher-guide)
- [Submission steps](https://aps.autodesk.com/marketplace/getting-started)
- [Revit guidelines](https://aps.autodesk.com/marketplace/publisher-center/revit-publisher-guidelines)
- [Product guidelines](https://apps.autodesk.com/Publisher/ProductGuidelines)
- [Declaration form](https://airtable.com/appHPAcNTdVz1ff79/pagR4kGoN4qjIYGGY/form)

The maintainer's publishing account is managed outside this repository; no account
details or secrets belong in the manifest or release archive.
