# REST API (optional service)

The API is an **optional layer** over the standalone translator and inventory agent. The core CLI remains dependency-free. The first API iteration provides PostgreSQL persistence, OIDC/JWT authentication, project-scoped source storage, durable database-backed jobs, and static inventory reports. It does not expose arbitrary command execution or run generated Python/COBOL.

## Architecture

```text
Client -> FastAPI / OpenAPI -> PostgreSQL (projects, sources, jobs, reports)
                                      ^
                                      |
                           separate polling worker
                                      |
                           cobol2py_agent.analyze_repository
```

The worker claims jobs with PostgreSQL `FOR UPDATE SKIP LOCKED`; multiple worker replicas can poll the same queue. API requests return `202 Accepted` for analyses and clients poll the job resource. Reports include the JSON inventory and Markdown plan produced by the existing agent.

## Local quick start

Requires Docker Compose.

```bash
cd api
docker compose up --build
```

Open the interactive API docs at <http://127.0.0.1:8000/docs>. For a local-only smoke test, set `COBOL2PY_API_ALLOW_ANONYMOUS=true` in the environment for the API service and recreate it. Do not enable anonymous access on a public network. The compose file binds ports to loopback by default and uses a development-only database password; override `POSTGRES_PASSWORD` for local environments that need a non-default value.

Example workflow:

```bash
# Development only; requires anonymous mode enabled in the API environment.
curl -sS -X POST http://127.0.0.1:8000/api/v1/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"legacy-billing"}'
# Use the returned project id as PROJECT_ID.
curl -sS -X POST "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/sources" \
  -H 'Content-Type: application/json' \
  -d '{"path":"src/main.cbl","content":"       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n       PROCEDURE DIVISION.\n           DISPLAY \"HELLO\".\n           STOP RUN.\n"}'
curl -sS -X POST "http://127.0.0.1:8000/api/v1/projects/$PROJECT_ID/analyses"
curl -sS "http://127.0.0.1:8000/api/v1/jobs/$JOB_ID"
curl -sS "http://127.0.0.1:8000/api/v1/reports/$REPORT_ID"
```

The API's own OpenAPI schema is available at `/openapi.json`; health checks are `/health/live` and `/health/ready`.

## Authentication

Configure these environment variables to require a JWT from an OIDC provider such as Amazon Cognito, Keycloak, or Auth0:

- `OIDC_ISSUER`: exact issuer URL expected in the token's `iss` claim.
- `OIDC_AUDIENCE`: expected API audience in the token's `aud` claim.
- `OIDC_JWKS_URL`: optional JWKS URL; defaults to `{OIDC_ISSUER}/.well-known/jwks.json`.

The current implementation verifies RS256/ES256 signatures, issuer, audience, expiry and subject. Project ownership is tied to the verified `sub` claim; requests for another subject's project return 404. Configure the provider to issue audience-bearing access tokens for this API. The current iteration implements owner isolation, not team membership/RBAC. `COBOL2PY_API_ALLOW_ANONYMOUS=true` is for loopback-only development and must remain false in production.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health/live` | Process liveness |
| GET | `/health/ready` | Database readiness |
| POST | `/api/v1/projects` | Create a project |
| GET | `/api/v1/projects` | List the caller's projects |
| POST | `/api/v1/projects/{id}/sources` | Create/update a source file |
| GET | `/api/v1/projects/{id}/sources` | List source metadata |
| POST | `/api/v1/projects/{id}/analyses` | Queue static inventory analysis (202) |
| GET | `/api/v1/jobs/{id}` | Poll job status |
| GET | `/api/v1/projects/{id}/reports` | List reports |
| GET | `/api/v1/reports/{id}` | Read report JSON and Markdown |

Source paths must be relative and cannot traverse outside the project workspace. Each request can store up to 2 MB of source text. Source content is held in PostgreSQL for this iteration; use private object storage and retention controls before accepting large estates or sensitive production source code.

## Data model

- `projects`: owner subject, name, creation timestamp.
- `source_files`: project, relative path, source text.
- `jobs`: status, kind and lifecycle timestamps.
- `reports`: JSON inventory and Markdown plan.

Tables are bootstrapped with SQLAlchemy `create_all` for the initial iteration. Before production rollout, add Alembic migrations and run schema changes as a separate deployment step; then set `COBOL2PY_API_AUTO_CREATE_SCHEMA=false`. Back up PostgreSQL, configure TLS/network policy, secret management, rate limits, request-size limits at the gateway, retention/deletion policy, and structured logs/metrics. The API uses synchronous SQLAlchemy sessions and should be deployed with worker processes sized to database capacity.

## Security and scope

- The worker performs static inventory only and never executes translated code.
- Differential validation is not exposed by this API; the repository's differential runner has a separate, explicit fixture-only execution policy.
- Run API and worker as non-root, restrict network egress, keep credentials out of images/logs, and place the database on a private network.
- Add RBAC/team memberships, audit events, idempotency keys, cancellation, and Alembic migrations before multi-tenant production use.
- The database queue is durable, but a worker crash after claiming a job can leave it in `running`; production hardening should add leases/heartbeat and stale-job recovery.
- The service is an optional deployment target. The standalone translator still needs only Python 3.10+ and `cobol2py.py`.
