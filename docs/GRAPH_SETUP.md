# Microsoft 365 setup for a firm (for the firm's IT provider)

What the firm's IT contact needs to do so the archive can read one SharePoint document library
and send reminders from one shared mailbox. Least privilege throughout. Research basis:
Prompt 14D and 14E (`docs/RESEARCH_FINDINGS.md`).

## Licensing

Business Standard is enough for both integrations below. Premium (Entra P1, Intune, Defender
for Business) is not required for the archive; it matters for the firm's own security posture,
which is a separate conversation (see `docs/COMPLIANCE_KIT.md`, "what not to claim").

## 1. App registration (once per firm)

1. Entra admin center → App registrations → New registration. Name it after the product;
   single tenant; no redirect URI (client-credentials flow).
2. Certificates & secrets → new client secret (or a certificate). Record tenant ID, client ID,
   secret in the firm's secret store; they go into the archive's environment as
   `MS_TENANT_ID`, `MS_CLIENT_ID`, `MS_CLIENT_SECRET`.

## 2. Reading one document library (connector)

- API permissions → Microsoft Graph → **Application** permission `Sites.Selected`. Grant admin
  consent. This grants access to no site until a site is explicitly assigned.
- Assign the site: with a Global or SharePoint admin, call
  `POST https://graph.microsoft.com/v1.0/sites/{site-id}/permissions` with
  `{"roles": ["read"], "grantedToIdentities": [{"application": {"id": "<client-id>", "displayName": "<app>"}}]}`
  (or use the PnP PowerShell `Grant-PnPAzureADAppSitePermission`). Read is enough; the archive
  never writes to SharePoint.
- Find the drive ID of the client-files library: `GET /sites/{site-id}/drives`. Put it in
  `GRAPH_DRIVE_ID`, and the folder path under it (for example `Clients`) in `GRAPH_ROOT_PATH`.
- First sync walks the folder; later syncs use the delta link, so only changed files are read.

## 3. Sending reminders from a shared mailbox

- Create or pick a shared mailbox, for example `documents@firm.com`. Put its address in
  `GRAPH_MAIL_FROM`.
- API permissions → Microsoft Graph → **Application** permission `Mail.Send`, admin consent.
- Restrict it to that one mailbox with an Exchange **Application Access Policy** (or the newer
  Exchange Application RBAC scope):
  `New-ApplicationAccessPolicy -AppId <client-id> -PolicyScopeGroupId documents@firm.com -AccessRight RestrictAccess`
  then `Test-ApplicationAccessPolicy` for a staff mailbox to confirm it is denied.
- SMTP AUTH is not needed and is off by default on tenants created after January 2020; Basic
  Auth for SMTP becomes disable-by-default after December 2026. Do not plan on it.

## 4. Google Workspace firms

Gmail API with domain-wide delegation to one service account, scoped to a single sending
address; Drive API for the connector. Same shape, different console.

## 5. What the firm can see

Every sync and every reminder is in the archive's audit log. The app registration's sign-in
logs in Entra show every token request. Revoking the client secret stops both integrations
immediately.
