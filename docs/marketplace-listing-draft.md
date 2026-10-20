# Marketplace listing draft

**Title:** MCP Server for Revit - Python

**Type:** Free desktop MCP connector; Windows 64-bit; local `stdio` server paired
with a pyRevit extension. No Autodesk endorsement or certification claimed.

**Short description:** Connect a local MCP client to Autodesk Revit for model
inspection, family placement, view visualization and reviewed Python automation.

**Description:**

MCP Server for Revit - Python is a free, MIT-licensed connector from the mcp-servers-for-revit organization. It connects a user-selected MCP client to Autodesk Revit through a local Python server and pyRevit extension. The connector exposes 20 tools for model inspection, visualization, family placement and reviewed automation.

Inspect project metadata, element counts, rooms, warnings, linked-model information, levels and elevations. List loaded family categories and types, inspect category parameters and sample values, and list exportable views. Read the active view's properties and visible elements, or export a named view as a PNG image. These responses help an MCP client understand the model before proposing an action.

For model changes, place an existing loaded family at supplied coordinates and set requested properties. Apply view color overrides using a parameter's values, or clear those overrides. Document tools can open, save, close or synchronize a model, using the options supplied in the request. Local discovery and launch tools help locate installed Revit versions and start an instance.

The Python tool executes supplied IronPython in Revit after the request is displayed for review. It runs with the Windows user's permissions and is not sandboxed: code can access files, unrelated data and network services. Approve only code you understand and use disposable models when evaluating unfamiliar automation.

Explicit Windows-user pairing is required. Choose Connect in the MCP Bridge panel to review the access notice. Modification and Python requests receive a separate prompt in Revit. Disconnect revokes subsequent calls; it cannot undo completed changes or recall responses. Your chosen AI client may forward tool responses to its provider, whose privacy and retention policies apply separately.

Publication review candidate: clean Revit 2027 validation, installer/dependency packaging and Autodesk decisions on Python execution, AI disclosures and licensing remain pending. No Autodesk endorsement or certification is claimed. See the linked privacy policy and repository documentation for data access, retention and limitations.

**License:** MIT; the repository retains its original attribution and license.

**Compatibility:** Revit 2027 is required for publication but has not been proven
for this PR by a live runtime test. Do not select compatibility checkboxes until
validation is recorded. pyRevit and Python 3.11+ are dependencies.

**Privacy URL:** The public `PRIVACY.md` URL for the final approved release. Do not
link a nonexistent default-branch document or claim a draft policy is published.

## Marketplace general usage instructions

1. Prepare the exact approved package on Windows 64-bit with Autodesk Revit, a supported pyRevit installation and Python 3.11 or later. This draft currently supplies source for review; final Marketplace installation instructions will follow Autodesk's packaging decision. Enable the extension and pyRevit Routes server using the repository instructions.

2. Open a disposable test model, or a model you are authorized to share with your chosen MCP client and its AI provider. In Revit, choose MCP > Bridge > Privacy to read the data-handling information, then Connect to review and accept the pairing notice. Pairing is shared by Revit instances running as the same Windows user.

3. Configure the MCP client with the exact extension directory and pinned dependencies. The repository example uses uv with arguments run, --frozen, --directory, the absolute extension path, python, and main.py. Keep stdio as the publication transport. When selecting among Revit instances, set REVIT_PORT to the desired instance's pyRevit Routes port. Do not place pairing secrets in client configuration or URLs.

4. Verify the client lists the 20 tools documented in the manifest. Begin with bridge status and model information. List levels, loaded family types and available views before requesting an export, placement or visualization. Review returned paths and model titles to confirm that the intended document is active.

5. For placement, colors, document lifecycle operations or Python automation, inspect the complete request in Revit before accepting it. Decline requests with unexpected files, destinations or changes. Python is unrestricted and can read or write files and contact network services. The prompt is a review control, not a sandbox. Test unfamiliar requests on a disposable model, and save a separate backup before accepting changes.

6. Inspect the result in Revit and the client's response. Check exported images, placed instances or view overrides as appropriate. A successful response alone does not validate every downstream effect. Do not synchronize test changes into a production central model.

7. Choose Disconnect when access is no longer wanted. Later calls should be refused. Reconnect rotates the pairing secret. Disconnect does not undo changes, stop every request already running or delete data retained by an AI client. Follow the privacy policy for temporary exports, host logs, saved models and client/provider deletion controls.

If setup fails, record the Revit/pyRevit versions and a non-confidential reproduction, then use the listed publisher support contact. Never share a pairing token or customer model in a public issue.

## Reviewer quick start for the source candidate

These steps validate the source candidate and are not a finished Marketplace
installer. Final dependency/bundle packaging must be agreed with Autodesk.

1. Install a supported pyRevit version into Revit 2027. Add the exact candidate
   checkout as a `.extension` folder and enable the extension/Routes server.
2. Start Revit with a non-confidential disposable test model. Confirm the MCP tab
   and Bridge panel exist. Choose Connect and review the consent notice.
3. From the candidate directory run `uv sync --frozen` followed by
   `uv run python main.py` as the chosen MCP client's stdio command. Use an absolute
   `--directory` path in client configuration so the exact candidate is selected.
4. Verify all manifest tools are listed. Test read tools, image export and all
   modification/lifecycle tools on disposable models. For writes/code, test both
   declining and accepting the Revit review prompt. Verify rollback/error behavior.
5. Choose Disconnect and verify tool calls are denied. Reconnect and verify old
   bearer headers are rejected. Confirm HTTP modes reject missing credentials and
   browser-originated requests. Never publish or paste the pairing token.
6. Remove the extension and Disconnect pairing; verify expected uninstall behavior
   and preserve user-created model files. Do not test destructive lifecycle actions
   on an unsaved or production model.

## Client example

```json
{
  "mcpServers": {
    "Revit Python": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "C:/path/to/revit-mcp-python.extension", "python", "main.py"]
    }
  }
}
```

For multiple Revit instances set `REVIT_PORT` to the selected instance's pyRevit
Routes port. All pairings for the same Windows user share one revocation boundary.
