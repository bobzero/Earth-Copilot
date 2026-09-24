# Microsoft Fabric integration

The container app exposes a small set of `/api/fabric/*` endpoints that
broker calls to Microsoft Fabric on behalf of the signed-in user (OAuth2
On-Behalf-Of flow). RLS / OLS / workspace ACLs are enforced by Fabric — the
backend never holds elevated privileges.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET  | `/api/fabric/status` | Reports whether the env vars are wired up. |
| GET  | `/api/fabric/workspaces` | Lists workspaces visible to the caller. |
| GET  | `/api/fabric/workspaces/{ws}/lakehouses` | Lists lakehouses in a workspace. |
| GET  | `/api/fabric/lakehouses/{ws}/{lh}/schema` | Returns the lakehouse table schema. |
| POST | `/api/fabric/query` | Executes a read-only SQL statement against a Lakehouse SQL endpoint. |
| POST | `/api/fabric/search_documents` | Semantic search across the customer's indexed document corpus. |

## Required environment variables

Set these on your backend container app (and any other env
where Fabric should be available):

| Var | Required | Default | Purpose |
|---|---|---|---|
| `FABRIC_TENANT_ID`   | yes (or `AZURE_TENANT_ID`) | — | AAD tenant for OBO token exchange. |
| `FABRIC_CLIENT_ID`   | yes | — | App registration client id. Needs delegated perms `Workspace.Read.All`, `Item.ReadWrite.All`, `Dataset.Read.All`. |
| `FABRIC_CLIENT_SECRET` | yes | — | Client secret (rotate via Key Vault). |
| `FABRIC_API_ENDPOINT` | no | `https://api.fabric.microsoft.com` | Override only for sovereign clouds. |
| `FABRIC_PBI_API_ENDPOINT` | no | `https://api.powerbi.com` | Override only for sovereign clouds. |
| `FABRIC_DOC_SEARCH_URL` | optional | — | Azure AI Search endpoint for `/api/fabric/search_documents`. |
| `FABRIC_DOC_SEARCH_KEY` | optional | — | AI Search admin/query key. |
| `FABRIC_DOC_SEARCH_INDEX` | optional | `planetary-explorer-docs` | Index name. |

If `FABRIC_CLIENT_ID` / `FABRIC_CLIENT_SECRET` are unset, all endpoints
return HTTP 503 with `"Fabric not configured"`. The UI surfaces this as a
muted card prompting the admin to finish setup — the rest of Planetary Explorer
keeps working.

## Auth model — OBO

1. User signs in through EasyAuth on the Container App. EasyAuth places the
   user's AAD access token in the `X-MS-TOKEN-AAD-ACCESS-TOKEN` request
   header.
2. The backend reads that header and exchanges it (via
   `urn:ietf:params:oauth:grant-type:jwt-bearer`) for a Fabric-scoped token
   using `FABRIC_CLIENT_ID` + `FABRIC_CLIENT_SECRET`.
3. The exchanged token (delegated, user-bound) is sent to the Fabric REST
   API. All authorization is evaluated by Fabric against the user.

The app registration must:

- Have the redirect URIs and EasyAuth configuration already used by the
  container app (no extra change needed there).
- Have **delegated** permissions on `Microsoft Fabric API` and `Power BI
  Service`:
  - `Workspace.Read.All`
  - `Item.ReadWrite.All`
  - `Dataset.Read.All`
- Have admin consent granted by a tenant admin for those permissions.

## Local dev

Without secrets:

```bash
uvicorn fastapi_app:app --reload
curl http://localhost:8000/api/fabric/status
# {"configured": false, "endpoint": "https://api.fabric.microsoft.com"}
```

With secrets set in `.env` and a signed-in user (the dev frontend should
forward the EasyAuth token as `Authorization: Bearer <token>` or via the
`X-MS-TOKEN-AAD-ACCESS-TOKEN` header), the `/api/fabric/workspaces` call
should return the user's workspaces.

## UI

The Sidebar renders a `FabricConnect` card under the Planetary Computer
search panel. The user selects a workspace + lakehouse; selection is
persisted in `localStorage` under `fabric.selection` and broadcast via a
`fabric:selection` custom event so other components (Chat, MapView) can
react.
