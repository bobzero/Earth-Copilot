# Planetary Explorer Deployment Security and Policy Overrides

This document records the security and subscription-specific changes retained while migrating the application from Earth Copilot to Planetary Explorer.

## Deployment constraints

- The target subscription does not permit deployment of new Azure AI services.
- The application uses the existing shared Azure OpenAI endpoint `https://expaoaieus2.openai.azure.com/` with the `gpt-4o` deployment.
- `deployAIFoundry` is therefore `false`. The template must not create an AI Services account, model deployments, an AI Hub, or an AI project.
- Shared-service authentication currently uses an API key because the deployed Container App has `USE_MANAGED_IDENTITY=false`. Store the key only in the GitHub environment secret `SHARED_AZURE_OPENAI_API_KEY` or an Azure secret store; never commit it.
- If the shared service grants the Container App identity access later, set `USE_MANAGED_IDENTITY=true` and remove the API-key secret.

## Preserved SFI controls

- Frontend authentication uses App Service EasyAuth and the Entra ID provider.
- The EasyAuth token store must be enabled so `/.auth/me` can supply the token used by the frontend API client.
- The backend uses `EntraAuthMiddleware` for protected routes. Container Apps EasyAuth stays disabled to avoid double validation and token-audience mismatches.
- The backend validates tenant issuers and accepted audiences and supports the EasyAuth `X-MS-CLIENT-PRINCIPAL` header plus a signed bearer-token fallback.
- Health, configuration, documentation, static assets, and server-generated tile routes remain explicitly allow-listed.
- HTTPS-only remains enabled on the frontend App Service.
- Container images use managed identity for ACR pull; anonymous and admin-user access must remain disabled where infrastructure policy supports it.
- Secrets must be supplied through GitHub environment secrets, Container App secrets, or Key Vault references. They must not be stored in parameter files.

## Authentication configuration

The deployment workflow expects:

| Setting | Storage | Purpose |
|---|---|---|
| `AUTH_CLIENT_ID` | GitHub environment secret | Entra application client ID used by frontend EasyAuth and backend token validation |
| `AZURE_TENANT_ID` | GitHub environment secret | Tenant used by deployment identity and backend issuer validation |
| `disable_auth` | Manual workflow input | Emergency/dev override; keep `false` for secured environments |
| `AUTH_AUTHORIZED_USERS` | GitHub environment variable | Optional comma-separated user allow-list |

When authentication is enabled, infrastructure and the post-deployment workflow pass `AZURE_AD_CLIENT_ID`, `AZURE_AD_TENANT_ID`, and `DISABLE_AUTH=false` to the backend. If authentication is intentionally disabled, infrastructure passes `DISABLE_AUTH=true`.

## Shared AI configuration

The deployment workflow uses these repository or environment settings:

| Setting | Default for this deployment |
|---|---|
| `DEPLOY_AI_FOUNDRY` | `false` |
| `SHARED_AZURE_OPENAI_ENDPOINT` | `https://expaoaieus2.openai.azure.com/` |
| `SHARED_AZURE_AI_PROJECT_ENDPOINT` | Empty unless a shared Foundry project is provided |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | `gpt-4o` |
| `AZURE_OPENAI_FAST_DEPLOYMENT` | `gpt-4o-mini` |
| `USE_MANAGED_IDENTITY` | `false` |
| `SHARED_AZURE_OPENAI_API_KEY` | GitHub environment secret; no default |

The backend deployment script prefers these configured shared-service values and does not search for or create an AI account in the application resource group. The Agent Service provisioning job runs only when `DEPLOY_AI_FOUNDRY=true`.

## Observed state before migration

The pre-migration Azure deployment was inspected on 2026-09-24:

- Backend Container App: `earth-copilot-exp` in `EXP-EarthCopilotDemo-RG`
- Shared Azure OpenAI endpoint: `https://expaoaieus2.openai.azure.com/`
- Model deployment: `gpt-4o`
- Backend settings: `USE_MANAGED_IDENTITY=false`, `DISABLE_AUTH=true`
- Frontend App Service: HTTPS-only enabled; EasyAuth disabled

The source retains the SFI authentication design, but the observed deployment was not enforcing it. Before treating the updated deployment as authenticated, configure `AUTH_CLIENT_ID`, re-run the workflow with `disable_auth=false`, and verify both EasyAuth and backend 401 behavior.

## Verification after deployment

1. Confirm unauthenticated frontend requests redirect to Entra sign-in.
2. Confirm `/.auth/me` returns an authenticated principal after sign-in.
3. Confirm an unauthenticated request to a protected backend route returns HTTP 401.
4. Confirm `/api/health` remains accessible without authentication.
5. Confirm the Container App uses the shared AI endpoint and no new AI Services account was created in the application resource group.
6. Run a satellite-data query and an agent query to verify both Azure OpenAI inference and any configured Foundry project endpoint.