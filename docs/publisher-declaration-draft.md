# MCP Publisher Declaration draft

This is a review draft, not a signed compliance declaration. Complete it against
the exact approved release and Autodesk's answers to the outstanding questions.

- **Architecture:** Local MCP Server (A), Windows, `stdio` publication transport.
- **Name:** MCP Server for Revit - Python.
- **Tools:** Use the 20 generated name/description entries in `mcp-tool-manifest.json`.
- **Resources/prompts:** None currently registered.
- **External data sources/endpoints:** Built-in client uses only the loopback pyRevit
  Routes API at `http://127.0.0.1:<selected-port>/revit_mcp`; no fixed internet API,
  database or publisher-hosted service. Model operations may open/synchronize
  user-selected network model locations. Supplied IronPython may initiate arbitrary
  connections. Destination enumeration and Local-model eligibility require Autodesk
  clarification. **Do not confirm all possible endpoints are enumerated.**
- **Autodesk data access/purpose:** Revit inspection, loaded-family placement, view
  export/coloring, document lifecycle and user-reviewed Python automation. See the
  manifest and privacy document for fields and API areas. Python's data scope is
  unrestricted; a minimum-data-only attestation cannot currently be made for it.
- **Categories/fields:** Model/project identifiers, client names, file/network paths,
  rooms/levels/elements/parameters, geometry, views/images, linked-model information,
  Revit installation locations and diagnostic errors. Arbitrary code can handle
  other categories. Review the form's current choices against the actual package.
- **Retention:** Ordinary responses in process memory per request; no connector
  response database. Pairing persists until Disconnect. Images are temporarily
  exported with cleanup attempts per request. Revit/pyRevit/client logs may retain
  diagnostics; no timed deletion is imposed. Saved models and arbitrary code output
  persist under user control. Do not answer simply 'Not retained' for all categories.
- **Age/minors:** No dedicated age/date-of-birth collection; professional adult use.
  Model fields/supplied code are not restricted to a fixed set of data categories.
- **AI:** No provider API called by the built-in MCP server. Responses are returned
  to the user-selected MCP client, which may forward them to its AI provider. The
  Connect notice discloses this boundary. Confirm with Autodesk how a local connector
  should answer the form's AI-transfer question and provider enumeration.
- **Dynamic remote tool loading:** No. Tools are registered from local packaged
  modules. Python execution is a declared tool, not a remote configuration service;
  whether it is acceptable is a separate Autodesk decision.
- **Storage/deletion:** See `PRIVACY.md`; DPAPI CurrentUser pairing file, transient
  export directories, user-selected model files and host/client logs.
- **Certifications:** None claimed.
- **Compliance confirmation:** Pending security scan, Revit 2027 runtime proof,
  packaging agreement, publisher validation and decisions on Python/loopback/AI.

Do not submit this draft or check a conflicting attestation to get past the form.
